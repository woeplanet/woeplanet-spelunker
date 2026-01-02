"""
WOEplanet Spelunker: dependencies package; database module.
"""

import json
import logging
import math
import random
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiosqlite
from aiosqlitepool import SQLiteConnectionPool
from starlette.exceptions import HTTPException
from starlette.requests import Request

if TYPE_CHECKING:
    from starlette.applications import Starlette

from woeplanet.spelunker.common.profiling import profile_async
from woeplanet.spelunker.dependencies.cache import disk_cache

logger = logging.getLogger(__name__)


@dataclass
class PlaceFilters:
    """
    Database place query filters
    """

    centroid: bool = True
    bounding_box: bool = True
    geometry: bool = True
    null_island: bool = False
    deprecated: bool = False
    exclude_placetypes: list[int] = field(default_factory=lambda: [0, 11, 25])
    ancestors: bool = True
    hierarchy: bool = True
    names: bool = True
    neighbours: bool = True
    children: bool = True
    history: bool = False
    licensing: bool = False


@dataclass
class SearchFilters:
    """
    Database search query filters
    """

    deprecated: bool = False
    unknown: bool = False
    null_island: bool = False


@dataclass
class FilterOptions:
    """
    Options for applying search filters to queries.
    """

    table_alias: str = 'p'
    geometry_join_exists: bool = False
    include_null_island: bool = True
    include_unknown: bool = True


def apply_search_filters(
    filters: SearchFilters,
    joins: list[str],
    where_clauses: list[str],
    options: FilterOptions | None = None,
) -> None:
    """
    Apply search filters to query joins and where clauses.
    """

    opts = options or FilterOptions()

    if not filters.deprecated:
        joins.append(f'LEFT JOIN changes ch ON {opts.table_alias}.woe_id = ch.woe_id')
        where_clauses.append('(ch.superseded_by IS NULL OR ch.woe_id IS NULL)')

    if opts.include_null_island and not filters.null_island:
        if not opts.geometry_join_exists:
            joins.append(f'LEFT JOIN geometries.geometries g ON {opts.table_alias}.woe_id = g.woe_id')
        where_clauses.append('(g.lat IS NOT NULL AND g.lng IS NOT NULL)')

    if opts.include_unknown and not filters.unknown:
        where_clauses.append(f'{opts.table_alias}.placetype_id != 0')


@dataclass
class PaginatedResult:
    """
    Paginated query result.
    """

    items: list[dict[str, Any]]
    has_more: bool


def _make_search_filter_cache_key(prefix: str) -> Callable[..., str]:
    """
    Return a cache key builder for a prefix and search filters
    """

    def key_builder(*, filters: SearchFilters) -> str:
        return f'{prefix}:{filters.deprecated}:{filters.unknown}:{filters.null_island}'

    return key_builder


def _make_cache_key(prefix: str) -> Callable[..., str]:
    """
    Return a vanilla cache key builder for a prefix
    """

    def key_builder() -> str:
        return f'{prefix}'

    return key_builder


class Database:
    """
    Wrapper around aiosqlite.Connection
    """

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn
        self._conn.row_factory = aiosqlite.Row

    async def _do_pagination_query(  # noqa: PLR0913
        self,
        select_cols: list[str],
        joins: list[str],
        where_clauses: list[str],
        params: list[Any],
        *,
        after: int | None = None,
        before: int | None = None,
        limit: int = 50,
    ) -> PaginatedResult:
        """
        Execute a keyset-paginated query on places table.
        """

        if before:
            where_clauses.append('p.woe_id < ?')
            params.append(before)
            order = 'DESC'
        elif after:
            where_clauses.append('p.woe_id > ?')
            params.append(after)
            order = 'ASC'
        else:
            order = 'ASC'

        params.append(limit + 1)

        query = f"""
            SELECT {', '.join(select_cols)}
            FROM places p
            {' '.join(joins)}
            WHERE {' AND '.join(where_clauses)}
            ORDER BY p.woe_id {order}
            LIMIT ?
        """  # noqa: S608

        logger.debug('%s - %s', query, params)
        cursor = await self._conn.execute(query, params)
        rows = [dict(r) for r in await cursor.fetchall()]

        has_more = len(rows) > limit
        items = rows[:limit]

        if before:
            items = items[::-1]

        return PaginatedResult(items=items, has_more=has_more)

    async def _do_count_query(
        self,
        joins: list[str],
        where_clauses: list[str],
        params: list[Any],
    ) -> int:
        """
        Execute a count query on places table.
        """

        query = f"""
            SELECT COUNT(*)
            FROM places p
            {' '.join(joins)}
            WHERE {' AND '.join(where_clauses)}
        """  # noqa: S608

        cursor = await self._conn.execute(query, params)
        row = await cursor.fetchone()
        return row[0] if row else 0

    @profile_async
    async def get_place_by_id(  # noqa: C901, PLR0912, PLR0915
        self,
        woe_id: int,
        filters: PlaceFilters,
    ) -> dict[str, Any] | None:
        """
        Get a place by WOEID
        """

        select_cols = ['p.*', 'pt.shortname as placetype_name']
        joins: list[str] = ['JOIN placetypes pt ON p.placetype_id = pt.id']
        where_clauses = ['p.woe_id = ?']
        params: list[Any] = [woe_id]
        json_fields: list[str] = []

        needs_geometry_join = filters.centroid or filters.bounding_box or filters.geometry or filters.null_island

        if needs_geometry_join:
            joins.append('LEFT JOIN geometries.geometries g ON p.woe_id = g.woe_id')

            if filters.centroid:
                select_cols.extend(['g.lat', 'g.lng'])
            if filters.bounding_box:
                select_cols.extend(['g.sw_lat', 'g.sw_lng', 'g.ne_lat', 'g.ne_lng'])
            if filters.geometry:
                select_cols.append('AsGeoJSON(g.geom) as geom')

        if filters.null_island:
            where_clauses.append('(g.lat IS NOT NULL AND g.lng IS NOT NULL AND g.geom IS NOT NULL)')

        if filters.deprecated:
            joins.append('LEFT JOIN changes ch ON p.woe_id = ch.woe_id')
            where_clauses.append('(ch.superseded_by IS NULL OR ch.woe_id IS NULL)')
        else:
            joins.append('LEFT JOIN changes ch ON p.woe_id = ch.woe_id')
            select_cols.extend(['ch.superseded_by', 'ch.supersedes'])
            json_fields.append('supersedes')

        if filters.exclude_placetypes:
            placeholders = ','.join('?' * len(filters.exclude_placetypes))
            where_clauses.append(f'p.placetype_id NOT IN ({placeholders})')
            params.extend(filters.exclude_placetypes)

        if filters.ancestors:
            select_cols.append("""
                (
                    SELECT json_group_array(ancestor_woe_id)
                    FROM ancestors
                    WHERE woe_id = p.woe_id
                ) as ancestors""")
            json_fields.append('ancestors')

        if filters.hierarchy:
            select_cols.append("""
                (
                    SELECT json_object(
                        'continent', json_object('woe_id', a.continent, 'name', p_cont.name),
                        'country', json_object('woe_id', a.country, 'name', p_coun.name),
                        'state', json_object('woe_id', a.state, 'name', p_state.name),
                        'county', json_object('woe_id', a.county, 'name', p_county.name),
                        'local_admin', json_object('woe_id', a.local_admin, 'name', p_la.name)
                    )
                    FROM admins a
                    LEFT JOIN places p_cont ON a.continent = p_cont.woe_id
                    LEFT JOIN places p_coun ON a.country = p_coun.woe_id
                    LEFT JOIN places p_state ON a.state = p_state.woe_id
                    LEFT JOIN places p_county ON a.county = p_county.woe_id
                    LEFT JOIN places p_la ON a.local_admin = p_la.woe_id
                    WHERE a.woe_id = p.woe_id
                ) as hierarchy""")
            json_fields.append('hierarchy')

        if filters.neighbours:
            select_cols.append("""
                (
                    SELECT json_group_array(neighbor_woe_id)
                    FROM neighbors
                    WHERE woe_id = p.woe_id
                ) as neighbours""")
            json_fields.append('neighbours')

        if filters.children:
            select_cols.append("""
                (
                    SELECT json_group_array(child_woe_id)
                    FROM children
                    WHERE woe_id = p.woe_id
                ) as children""")
            json_fields.append('children')

        if filters.names:
            select_cols.append("""
                (
                    SELECT json_group_array(
                        json_object(
                            'name', name,
                            'name_type', name_type,
                            'language', language
                        )
                    )
                    FROM aliases
                    WHERE woe_id = p.woe_id
                ) as aliases""")
            json_fields.append('aliases')

        if filters.history:
            joins.append('LEFT JOIN history hist ON p.woe_id = hist.woe_id')
            select_cols.append('hist.history')
            json_fields.append('history')

        if filters.licensing:
            joins.append('LEFT JOIN licensing lic ON p.woe_id = lic.woe_id')
            select_cols.append('lic.licenses')
            json_fields.append('licenses')

        query = f"""
            SELECT {', '.join(select_cols)}
            FROM places p
            {' '.join(joins)}
            WHERE {' AND '.join(where_clauses)}
        """  # noqa: S608

        logger.debug('%s - %s', query, params)
        cursor = await self._conn.execute(query, params)
        row = await cursor.fetchone()
        if row is None:
            return None

        result = dict(row)
        for json_field in json_fields:
            if result[json_field]:
                result[json_field] = json.loads(result[json_field])
            else:
                result[json_field] = None if json_field == 'hierarchy' else []

        if filters.names and result.get('aliases'):
            result['aliases'] = self.inflate_aliases(result['aliases'])

        return result

    def inflate_aliases(self, aliases: list[dict[str, str]]) -> dict[str, dict[str, set[str]]]:
        """
        Inflate aliases, grouped by language and then alias type

        name_type codes:
            S - Standard/Official name
            P - Preferred name
            V - Variant name
            Q - Colloquial name
            A - Abbreviation
        """

        name_type_order = ['S', 'P', 'V', 'Q', 'A']

        grouped: dict[str, dict[str, set[str]]] = {}
        for alias in aliases:
            lang = alias['language']
            name_type = alias['name_type']
            name = alias['name']

            if lang not in grouped:
                grouped[lang] = {nt: set() for nt in name_type_order}

            if name_type in grouped[lang]:
                grouped[lang][name_type].add(name)

        return grouped

    @profile_async
    async def inflate_place_ids(self, woe_ids: list[int]) -> dict[str, list[dict[str, Any]]]:
        """
        Inflate WOEIDs into places grouped by placetype
        """

        if not woe_ids:
            return {}

        placeholders = ','.join('?' * len(woe_ids))
        query = f"""
            SELECT
                p.woe_id,
                p.name,
                p.placetype_id,
                pt.name as placetype_name,
                pt.shortname as placetype_shortname
            FROM places p
            JOIN placetypes pt ON p.placetype_id = pt.id
            WHERE p.woe_id IN ({placeholders})
        """  # noqa: S608

        logger.debug('%s - %s', query, woe_ids)
        cursor = await self._conn.execute(query, woe_ids)
        rows = await cursor.fetchall()

        result: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            place = {
                'woe_id': row['woe_id'],
                'name': row['name'],
                'placetype_id': row['placetype_id'],
                'placetype_name': row['placetype_name'],
            }
            ptname = row['placetype_name']
            if ptname not in result:
                result[ptname] = []
            result[ptname].append(place)

        return result

    @disk_cache(key_builder=_make_search_filter_cache_key('countries_facets'))
    @profile_async
    async def get_countries_facets(self, *, filters: SearchFilters) -> list[dict[str, Any]]:
        """
        Get all countries with place counts
        """

        joins = ['LEFT JOIN admins a ON a.country = c.woe_id']
        where_clauses: list[str] = []

        if not filters.deprecated:
            joins.append('LEFT JOIN changes ch ON a.woe_id = ch.woe_id')
            where_clauses.append('(ch.superseded_by IS NULL OR ch.woe_id IS NULL)')

        if not filters.null_island:
            joins.append('LEFT JOIN geometries.geometries g ON a.woe_id = g.woe_id')
            where_clauses.append('(g.lat IS NOT NULL AND g.lng IS NOT NULL)')

        if not filters.unknown:
            joins.append('LEFT JOIN places p ON a.woe_id = p.woe_id')
            where_clauses.append('p.placetype_id != 0')

        where_sql = f'WHERE {" AND ".join(where_clauses)}' if where_clauses else ''

        query = f"""
            SELECT
                c.woe_id,
                c.name,
                c.iso2,
                COUNT(a.woe_id) as count
            FROM countries c
            {' '.join(joins)}
            {where_sql}
            GROUP BY c.woe_id, c.name, c.iso2
            ORDER BY count DESC, c.name
        """  # noqa: S608

        logger.debug('%s - %s', query, {})
        cursor = await self._conn.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    @disk_cache(key_builder=_make_search_filter_cache_key('total_woeids'))
    @profile_async
    async def get_total_woeids(self, *, filters: SearchFilters) -> int:
        """
        Get the total number of WOEIDs
        """

        joins: list[str] = []
        where_clauses: list[str] = []
        apply_search_filters(filters, joins, where_clauses)
        where_sql = f'WHERE {" AND ".join(where_clauses)}' if where_clauses else ''

        query = f"""
            SELECT COUNT(*)
            FROM places p
            {' '.join(joins)}
            {where_sql}
        """  # noqa: S608

        logger.debug('%s - %s', query, {})
        cursor = await self._conn.execute(query)
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail='Database integrity error: cannot get number of WOEIDs',
            )

        return row[0]

    @disk_cache(key_builder=_make_search_filter_cache_key('placetypes_facets'))
    @profile_async
    async def get_placetype_facets(self, *, filters: SearchFilters) -> list[dict[str, Any]]:
        """
        Get all placetypes with place counts
        """

        logger.debug('get_placetype_facets: filters=%s', filters)
        joins = ['JOIN placetypes pt ON p.placetype_id = pt.id']
        where_clauses: list[str] = []
        apply_search_filters(filters, joins, where_clauses)
        where_sql = f'WHERE {" AND ".join(where_clauses)}' if where_clauses else ''

        query = f"""
            SELECT
                p.placetype_id,
                pt.shortname,
                pt.name,
                COUNT(*) as count
            FROM places p
            {' '.join(joins)}
            {where_sql}
            GROUP BY p.placetype_id, pt.shortname
            ORDER BY count DESC
        """  # noqa: S608

        logger.debug('%s - %s', query, {})
        cursor = await self._conn.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    def _build_placetype_query(
        self,
        placetype_id: int,
        *,
        include_geometry: bool = True,
    ) -> tuple[list[str], list[str], list[Any], FilterOptions]:
        """
        Build query parts for placetype queries.
        """

        joins = ['JOIN placetypes pt ON p.placetype_id = pt.id']
        if include_geometry:
            joins.append('LEFT JOIN geometries.geometries g ON p.woe_id = g.woe_id')
        where_clauses = ['p.placetype_id = ?']
        params: list[Any] = [placetype_id]
        opts = FilterOptions(geometry_join_exists=include_geometry, include_unknown=False)
        return joins, where_clauses, params, opts

    @profile_async
    async def get_places_by_placetype(
        self,
        placetype_id: int,
        *,
        filters: SearchFilters,
        after: int | None = None,
        before: int | None = None,
        limit: int = 50,
    ) -> PaginatedResult:
        """
        Get places by placetype with keyset pagination.
        """

        select_cols = [
            'p.woe_id',
            'p.name',
            'pt.shortname as placetype_name',
            'g.lat',
            'g.lng',
            'g.sw_lat',
            'g.sw_lng',
            'g.ne_lat',
            'g.ne_lng',
        ]
        joins, where_clauses, params, opts = self._build_placetype_query(placetype_id)
        apply_search_filters(filters, joins, where_clauses, opts)

        return await self._do_pagination_query(
            select_cols,
            joins,
            where_clauses,
            params,
            after=after,
            before=before,
            limit=limit,
        )

    @profile_async
    async def get_places_by_placetype_count(
        self,
        placetype_id: int,
        *,
        filters: SearchFilters,
    ) -> int:
        """
        Get count of places for a placetype.
        """

        joins, where_clauses, params, opts = self._build_placetype_query(placetype_id, include_geometry=False)
        apply_search_filters(filters, joins, where_clauses, opts)

        return await self._do_count_query(joins, where_clauses, params)

    @profile_async
    async def get_country_by_iso(self, iso: str) -> dict[str, Any] | None:
        """
        Get a country by ISO 3166-1 alpha-2 code.
        """

        iso_upper = iso.upper()
        query = """
            SELECT woe_id, name, iso2, iso3
            FROM countries
            WHERE UPPER(iso2) = ?
        """
        logger.debug('%s - %s', query, (iso_upper,))
        cursor = await self._conn.execute(query, (iso_upper,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    def _build_country_query(
        self,
        country_woe_id: int,
        placetype: str | None,
        *,
        include_geometry: bool = True,
    ) -> tuple[list[str], list[str], list[Any], FilterOptions]:
        """
        Build query parts for country queries.
        """

        joins = ['JOIN admins a ON p.woe_id = a.woe_id']
        if include_geometry:
            joins.insert(0, 'JOIN placetypes pt ON p.placetype_id = pt.id')
            joins.append('LEFT JOIN geometries.geometries g ON p.woe_id = g.woe_id')
        where_clauses = ['a.country = ?']
        params: list[Any] = [country_woe_id]

        if placetype:
            joins.append('JOIN placetypes pt_filter ON p.placetype_id = pt_filter.id')
            where_clauses.append('LOWER(pt_filter.shortname) = ?')
            params.append(placetype.lower())

        opts = FilterOptions(geometry_join_exists=include_geometry)
        return joins, where_clauses, params, opts

    @profile_async
    async def get_places_by_country(  # noqa: PLR0913
        self,
        country_woe_id: int,
        *,
        filters: SearchFilters,
        placetype: str | None = None,
        after: int | None = None,
        before: int | None = None,
        limit: int = 50,
    ) -> PaginatedResult:
        """
        Get places by country with keyset pagination.
        """

        select_cols = [
            'p.woe_id',
            'p.name',
            'pt.shortname as placetype_name',
            'g.lat',
            'g.lng',
            'g.sw_lat',
            'g.sw_lng',
            'g.ne_lat',
            'g.ne_lng',
        ]
        joins, where_clauses, params, opts = self._build_country_query(country_woe_id, placetype)
        apply_search_filters(filters, joins, where_clauses, opts)

        return await self._do_pagination_query(
            select_cols,
            joins,
            where_clauses,
            params,
            after=after,
            before=before,
            limit=limit,
        )

    @disk_cache(
        key_builder=lambda country_woe_id, filters, placetype=None: (
            f'country_count:{country_woe_id}:{placetype}:{filters.deprecated}:{filters.unknown}:{filters.null_island}'
        ),
    )
    @profile_async
    async def get_places_by_country_count(
        self,
        *,
        country_woe_id: int,
        filters: SearchFilters,
        placetype: str | None = None,
    ) -> int:
        """
        Get count of places for a country.
        """

        joins, where_clauses, params, opts = self._build_country_query(
            country_woe_id,
            placetype,
            include_geometry=False,
        )
        apply_search_filters(filters, joins, where_clauses, opts)

        return await self._do_count_query(joins, where_clauses, params)

    @disk_cache(
        key_builder=lambda iso2, filters: (
            f'placetypes_by_country:{iso2.upper()}:{filters.deprecated}:{filters.unknown}:{filters.null_island}'
        ),
    )
    @profile_async
    async def get_placetypes_by_country(
        self,
        *,
        iso2: str,
        filters: SearchFilters,
    ) -> list[dict[str, Any]]:
        """
        Get placetype facets (buckets with counts) for a given ISO2 country code.
        """

        country = await self.get_country_by_iso(iso2)
        if not country:
            return []

        country_woe_id = country['woe_id']

        joins = [
            'JOIN places p ON a.woe_id = p.woe_id',
            'JOIN placetypes pt ON p.placetype_id = pt.id',
        ]
        where_clauses = ['a.country = ?']
        params: list[Any] = [country_woe_id]
        apply_search_filters(filters, joins, where_clauses, FilterOptions(table_alias='p'))

        query = f"""
            SELECT
                p.placetype_id,
                pt.shortname,
                pt.name,
                COUNT(*) as count
            FROM admins a
            {' '.join(joins)}
            WHERE {' AND '.join(where_clauses)}
            GROUP BY p.placetype_id, pt.shortname, pt.name
            ORDER BY count DESC
        """  # noqa: S608

        logger.debug('%s - %s', query, params)
        cursor = await self._conn.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    def _build_nullisland_query(
        self,
        *,
        include_placetype: bool = True,
    ) -> tuple[list[str], list[str], list[Any], FilterOptions]:
        """
        Build query parts for null island queries.
        """

        joins = ['LEFT JOIN geometries.geometries g ON p.woe_id = g.woe_id']
        if include_placetype:
            joins.insert(0, 'JOIN placetypes pt ON p.placetype_id = pt.id')
        where_clauses = ['(g.lat IS NULL OR g.lng IS NULL OR (g.lat = 0 AND g.lng = 0))']
        params: list[Any] = []
        opts = FilterOptions(geometry_join_exists=True, include_null_island=False)
        return joins, where_clauses, params, opts

    @profile_async
    async def get_nullisland_places(
        self,
        *,
        filters: SearchFilters,
        after: int | None = None,
        before: int | None = None,
        limit: int = 50,
    ) -> PaginatedResult:
        """
        Get places that visit Null Island (null or zero coordinates) with keyset pagination.
        """

        select_cols = [
            'p.woe_id',
            'p.name',
            'pt.shortname as placetype_name',
            'g.lat',
            'g.lng',
        ]
        joins, where_clauses, params, opts = self._build_nullisland_query()
        apply_search_filters(filters, joins, where_clauses, opts)

        return await self._do_pagination_query(
            select_cols,
            joins,
            where_clauses,
            params,
            after=after,
            before=before,
            limit=limit,
        )

    @profile_async
    async def get_nullisland_places_count(self, *, filters: SearchFilters) -> int:
        """
        Get count of places that visit Null Island.
        """

        joins, where_clauses, params, opts = self._build_nullisland_query(include_placetype=False)
        apply_search_filters(filters, joins, where_clauses, opts)

        return await self._do_count_query(joins, where_clauses, params)

    @profile_async
    async def get_nullisland_placetype_facets(self, *, filters: SearchFilters) -> list[dict[str, Any]]:
        """
        Get placetype facets for Null Island places.
        """

        joins = [
            'JOIN placetypes pt ON p.placetype_id = pt.id',
            'LEFT JOIN geometries.geometries g ON p.woe_id = g.woe_id',
        ]
        where_clauses = ['(g.lat IS NULL OR g.lng IS NULL OR (g.lat = 0 AND g.lng = 0))']
        apply_search_filters(
            filters,
            joins,
            where_clauses,
            FilterOptions(geometry_join_exists=True, include_null_island=False),
        )

        query = f"""
            SELECT
                p.placetype_id,
                pt.shortname,
                pt.name,
                COUNT(*) as count
            FROM places p
            {' '.join(joins)}
            WHERE {' AND '.join(where_clauses)}
            GROUP BY p.placetype_id, pt.shortname, pt.name
            ORDER BY count DESC
        """  # noqa: S608

        logger.debug('%s', query)
        cursor = await self._conn.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    @profile_async
    async def search_places(  # noqa: PLR0913
        self,
        query_text: str,
        *,
        name_type: str | None = None,
        filters: SearchFilters,
        after: int | None = None,
        before: int | None = None,
        limit: int = 50,
    ) -> PaginatedResult:
        """
        Search places with optional name_type filter and keyset pagination.
        """

        params: list[Any] = [query_text]
        where_clauses = ['fts.name MATCH ?']

        if name_type and name_type != 'any':
            where_clauses.append('a.name_type = ?')
            params.append(name_type)

        if before:
            where_clauses.append('a.woe_id < ?')
            params.append(before)
            order = 'DESC'
        elif after:
            where_clauses.append('a.woe_id > ?')
            params.append(after)
            order = 'ASC'
        else:
            order = 'ASC'

        params.append(limit + 1)

        query = f"""
            SELECT
                a.woe_id,
                a.name as alias_name,
                a.name_type,
                a.language,
                fts.rank
            FROM aliases_fts fts
            JOIN aliases a ON fts.rowid = a.rowid
            WHERE {' AND '.join(where_clauses)}
            GROUP BY a.woe_id
            HAVING MIN(CASE a.name_type
                WHEN 'S' THEN 1 WHEN 'P' THEN 2 WHEN 'V' THEN 3
                WHEN 'Q' THEN 4 WHEN 'A' THEN 5 ELSE 6 END)
            ORDER BY a.woe_id {order}
            LIMIT ?
        """  # noqa: S608

        logger.debug('%s - %s', query, params)
        try:
            cursor = await self._conn.execute(query, params)
            search_rows = [dict(r) for r in await cursor.fetchall()]
        except Exception:
            logger.exception('Search query failed')
            return PaginatedResult(items=[], has_more=False)

        if not search_rows:
            return PaginatedResult(items=[], has_more=False)

        has_more = len(search_rows) > limit
        search_rows = search_rows[:limit]
        if before:
            search_rows = search_rows[::-1]

        woe_ids = [r['woe_id'] for r in search_rows]
        places = await self._enrich_search_results(woe_ids, filters)

        items = []
        for row in search_rows:
            woe_id = row['woe_id']
            if woe_id in places:
                item = {**row, **places[woe_id]}
                items.append(item)

        return PaginatedResult(items=items, has_more=has_more)

    async def _enrich_search_results(self, woe_ids: list[int], filters: SearchFilters) -> dict[int, dict[str, Any]]:
        """
        Enrich search results with place details, filtering as needed.
        """

        if not woe_ids:
            return {}

        placeholders = ','.join('?' * len(woe_ids))
        params: list[Any] = list(woe_ids)

        joins = [
            'JOIN placetypes pt ON p.placetype_id = pt.id',
            'LEFT JOIN geometries.geometries g ON p.woe_id = g.woe_id',
            'LEFT JOIN admins ad ON p.woe_id = ad.woe_id',
            'LEFT JOIN countries c ON ad.country = c.woe_id',
        ]
        where_clauses = [f'p.woe_id IN ({placeholders})']
        apply_search_filters(filters, joins, where_clauses, FilterOptions(geometry_join_exists=True))

        query = f"""
            SELECT
                p.woe_id,
                p.name,
                pt.shortname as placetype_name,
                g.lat,
                g.lng,
                c.name as country_name
            FROM places p
            {' '.join(joins)}
            WHERE {' AND '.join(where_clauses)}
            GROUP BY p.woe_id
        """  # noqa: S608

        cursor = await self._conn.execute(query, params)
        rows = await cursor.fetchall()

        return {row['woe_id']: dict(row) for row in rows}

    @profile_async
    async def search_places_count(
        self,
        query_text: str,
        *,
        name_type: str | None = None,
        filters: SearchFilters,
    ) -> int:
        """
        Get count of search results.
        """

        joins = [
            'JOIN aliases a ON p.woe_id = a.woe_id',
            'JOIN aliases_fts fts ON a.rowid = fts.rowid',
            'LEFT JOIN geometries.geometries g ON p.woe_id = g.woe_id',
        ]
        where_clauses = ['fts.name MATCH ?']
        params: list[Any] = [query_text]

        if name_type and name_type != 'any':
            where_clauses.append('a.name_type = ?')
            params.append(name_type)

        apply_search_filters(filters, joins, where_clauses, FilterOptions(geometry_join_exists=True))

        query = f"""
            SELECT COUNT(DISTINCT p.woe_id)
            FROM places p
            {' '.join(joins)}
            WHERE {' AND '.join(where_clauses)}
        """  # noqa: S608

        logger.debug('%s - %s', query, params)
        try:
            cursor = await self._conn.execute(query, params)
            row = await cursor.fetchone()
            return row[0] if row else 0
        except Exception:
            logger.exception('Search count query failed')
            return 0

    @disk_cache(key_builder=_make_cache_key('placetypes'))
    @profile_async
    async def get_placetypes(self) -> list[dict[str, Any]]:
        """
        Get all placetypes
        """

        query = 'SELECT * FROM placetypes'
        cursor = await self._conn.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    @profile_async
    async def get_licenses(self) -> list[dict[str, Any]]:
        """
        Get all licenses
        """

        query = 'SELECT * FROM licenses'
        cursor = await self._conn.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def _get_woeid_range(self) -> tuple[int, int]:
        """
        Get min/max woe_id range from places table.
        """

        cursor = await self._conn.execute('SELECT MIN(woe_id), MAX(woe_id) FROM places')
        row = await cursor.fetchone()
        if not row or row[0] is None:
            return (0, 0)
        return (row[0], row[1])

    async def _is_valid_random_place(self, woe_id: int, filters: PlaceFilters) -> bool:
        """
        Check if a woe_id passes the random place filters.
        """

        if not filters.null_island:
            cursor = await self._conn.execute(
                'SELECT 1 FROM geometries.geometries WHERE woe_id = ? AND lat IS NOT NULL AND lng IS NOT NULL',
                (woe_id,),
            )
            if not await cursor.fetchone():
                return False

        if not filters.deprecated:
            cursor = await self._conn.execute(
                'SELECT 1 FROM changes WHERE woe_id = ? AND superseded_by IS NOT NULL',
                (woe_id,),
            )
            if await cursor.fetchone():
                return False

        return True

    @profile_async
    async def get_random_place(self, filters: PlaceFilters) -> dict[str, Any] | None:
        """
        Get a random place using woe_id range sampling (O(log n) index seek).
        """

        min_id, max_id = await self._get_woeid_range()
        if min_id == 0 and max_id == 0:
            return None

        where_clauses = ['woe_id >= ?']
        params: list[Any] = []

        if filters.exclude_placetypes:
            placeholders = ','.join('?' * len(filters.exclude_placetypes))
            where_clauses.append(f'placetype_id NOT IN ({placeholders})')
            params.extend(filters.exclude_placetypes)

        select_sql = f"""
            SELECT woe_id FROM places
            WHERE {' AND '.join(where_clauses)}
            LIMIT 1
        """  # noqa: S608

        max_attempts = 50
        for _ in range(max_attempts):
            random_id = random.randint(min_id, max_id)  # noqa: S311
            query_params = [random_id, *params]

            cursor = await self._conn.execute(select_sql, query_params)
            row = await cursor.fetchone()
            if row and await self._is_valid_random_place(row[0], filters):
                return dict(row)

        return None

    @profile_async
    async def get_places_near_centroid(  # noqa: PLR0913
        self,
        lat: float,
        lng: float,
        distance: int,
        filters: SearchFilters,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedResult:
        """
        Get places within a specified distance (in metres) of a point.
        """

        # Bounding box pre-filter: ~111km per degree latitude, adjusted for longitude
        lat_delta = distance / 111000.0
        lng_delta = distance / (111000.0 * max(math.cos(math.radians(lat)), 0.01))

        joins: list[str] = ['JOIN geometries.geometries g ON p.woe_id = g.woe_id']
        where_clauses: list[str] = [
            'g.lat BETWEEN ? AND ?',
            'g.lng BETWEEN ? AND ?',
        ]
        # MakePoint params first (lng, lat), then WHERE clause params
        params: list[Any] = [
            lng,
            lat,
            lat - lat_delta,
            lat + lat_delta,
            lng - lng_delta,
            lng + lng_delta,
        ]
        apply_search_filters(
            filters,
            joins,
            where_clauses,
            FilterOptions(geometry_join_exists=True, include_null_island=False, include_unknown=False),
        )

        query = f"""
            WITH origin AS (SELECT MakePoint(?, ?, 4326) AS pt),
            candidates AS (
                SELECT
                    p.woe_id,
                    p.name,
                    p.placetype_id,
                    pt.shortname as placetype_name,
                    g.lat,
                    g.lng,
                    ST_Distance(g.geom, origin.pt, 1) as distance_m
                FROM places p
                JOIN placetypes pt ON p.placetype_id = pt.id
                {' '.join(joins)}
                CROSS JOIN origin
                WHERE {' AND '.join(where_clauses)}
            )
            SELECT * FROM candidates
            WHERE distance_m <= ?
            ORDER BY distance_m ASC, woe_id ASC
            LIMIT ? OFFSET ?
        """  # noqa: S608

        params.extend([distance, limit + 1, offset])

        logger.debug('%s - %s', query, params)
        cursor = await self._conn.execute(query, params)
        rows = [dict(r) for r in await cursor.fetchall()]

        has_more = len(rows) > limit
        items = rows[:limit]

        return PaginatedResult(items=items, has_more=has_more)

    @profile_async
    async def get_places_near_centroid_count(
        self,
        lat: float,
        lng: float,
        distance: int,
        filters: SearchFilters,
    ) -> int:
        """
        Get count of places within a specified distance (in metres) of a point.
        """

        lat_delta = distance / 111000.0
        lng_delta = distance / (111000.0 * max(math.cos(math.radians(lat)), 0.01))

        joins: list[str] = ['JOIN geometries.geometries g ON p.woe_id = g.woe_id']
        where_clauses: list[str] = [
            'g.lat BETWEEN ? AND ?',
            'g.lng BETWEEN ? AND ?',
        ]
        # MakePoint params first (lng, lat), then WHERE clause params
        params: list[Any] = [
            lng,
            lat,
            lat - lat_delta,
            lat + lat_delta,
            lng - lng_delta,
            lng + lng_delta,
            distance,
        ]
        apply_search_filters(
            filters,
            joins,
            where_clauses,
            FilterOptions(geometry_join_exists=True, include_null_island=False, include_unknown=False),
        )

        query = f"""
            WITH origin AS (SELECT MakePoint(?, ?, 4326) AS pt),
            candidates AS (
                SELECT p.woe_id,
                    ST_Distance(g.geom, origin.pt, 1) as distance_m
                FROM places p
                {' '.join(joins)}
                CROSS JOIN origin
                WHERE {' AND '.join(where_clauses)}
            )
            SELECT COUNT(*) FROM candidates WHERE distance_m <= ?
        """  # noqa: S608

        logger.debug('%s - %s', query, params)
        cursor = await self._conn.execute(query, params)
        row = await cursor.fetchone()
        return row[0] if row else 0


async def create_connection_factory(
    db_path: Path,
    geom_db_path: Path,
) -> Callable[[], Coroutine[Any, Any, aiosqlite.Connection]]:
    """
    Create a connection factory function for the pool
    """

    async def connection_factory() -> aiosqlite.Connection:
        """
        Create and initialise a database connection with Spatialite support.
        """

        conn = await aiosqlite.connect(str(db_path))
        await conn.execute('ATTACH DATABASE ? AS geometries', (str(geom_db_path),))
        await conn.enable_load_extension(True)  # noqa: FBT003
        await conn.execute("SELECT load_extension('mod_spatialite')")
        await conn.enable_load_extension(False)  # noqa: FBT003

        return conn

    return connection_factory


async def init_pool(db_path: Path, geom_db_path: Path, pool_size: int = 10) -> SQLiteConnectionPool:
    """
    Create and return a database connection pool
    """

    factory = await create_connection_factory(db_path, geom_db_path)

    return SQLiteConnectionPool(
        connection_factory=factory,
        pool_size=pool_size,
    )


@asynccontextmanager
async def get_db(
    request: Request | None = None,
    app: 'Starlette | None' = None,
) -> AsyncIterator[Database]:
    """
    Get a database connection from the pool
    """

    if request is not None:
        pool = request.app.state.db_pool
    elif app is not None:
        pool = app.state.db_pool
    else:
        msg = 'Either request or app must be provided'
        raise ValueError(msg)

    async with pool.connection() as conn:
        yield Database(conn)
