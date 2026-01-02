"""
WOEplanet Spelunker: common package; pagination module.
"""

import math
from dataclasses import dataclass

from starlette.requests import Request

from woeplanet.spelunker.common.query_params import PaginationParams
from woeplanet.spelunker.dependencies.database import PaginatedResult


@dataclass
class PaginationUrls:
    """
    Pagination URL results.
    """

    prev: str | None
    next: str | None


@dataclass
class PaginationContext:
    """
    Full pagination context for templates.
    """

    total: int
    page: int
    pages: int
    urls: PaginationUrls


def build_pagination_context(
    request: Request,
    result: PaginatedResult,
    *,
    pagination: PaginationParams,
    total: int,
) -> PaginationContext:
    """
    Build full pagination context including page numbers (cursor-based).
    """

    prev_url = None
    next_url = None
    pages = max(1, math.ceil(total / pagination.limit))

    if result.items:
        first_id = result.items[0]['woe_id']
        last_id = result.items[-1]['woe_id']

        if result.has_more:
            next_url = str(
                request.url.remove_query_params(['before', 'page']).include_query_params(
                    after=last_id,
                    page=pagination.page + 1,
                ),
            )

        if pagination.page > 1:
            prev_url = str(
                request.url.remove_query_params(['after', 'page']).include_query_params(
                    before=first_id,
                    page=pagination.page - 1,
                ),
            )

    return PaginationContext(
        total=total,
        page=pagination.page,
        pages=pages,
        urls=PaginationUrls(prev=prev_url, next=next_url),
    )


def build_offset_pagination_context(
    request: Request,
    result: PaginatedResult,
    *,
    pagination: PaginationParams,
    total: int,
) -> PaginationContext:
    """
    Build full pagination context including page numbers (offset-based).
    """

    prev_url = None
    next_url = None
    pages = max(1, math.ceil(total / pagination.limit))

    if result.has_more:
        next_url = str(
            request.url.remove_query_params(['page']).include_query_params(
                page=pagination.page + 1,
            ),
        )

    if pagination.page > 1:
        prev_url = str(
            request.url.remove_query_params(['page']).include_query_params(
                page=pagination.page - 1,
            ),
        )

    return PaginationContext(
        total=total,
        page=pagination.page,
        pages=pages,
        urls=PaginationUrls(prev=prev_url, next=next_url),
    )
