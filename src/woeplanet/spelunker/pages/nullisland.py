"""
WOEplanet Spelunker: pages package; nullisland page module
"""

from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.common.pagination import build_pagination_context
from woeplanet.spelunker.common.query_params import parse_filter_params, parse_pagination
from woeplanet.spelunker.dependencies.database import get_db
from woeplanet.spelunker.dependencies.templates import get_templater


async def nullisland_endpoint(request: Request) -> HTMLResponse:
    """
    Null Island page endpoint
    """

    parsed = parse_filter_params(request)
    pagination = parse_pagination(request)

    async with get_db(request=request) as db:
        buckets = await db.get_nullisland_placetype_facets(filters=parsed.filters)
        total = await db.get_nullisland_places_count(filters=parsed.filters)
        result = await db.get_nullisland_places(
            filters=parsed.filters,
            after=pagination.after,
            before=pagination.before,
            limit=pagination.limit,
        )

    paging = build_pagination_context(request, result, pagination=pagination, total=total)

    template = get_templater().get_template('nullisland.html.j2')
    template_args = {
        'title': 'Null Island',
        'results': result.items,
        'total': total,
        'includes': parsed.includes,
        'includes_qs': parsed.query_string,
        'map': False,
        'pagination': paging,
        'buckets': buckets,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content)
