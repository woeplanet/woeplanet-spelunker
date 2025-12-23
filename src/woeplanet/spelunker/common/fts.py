"""
WOEplanet Spelunker: common package; FTS query sanitisation module.
"""

import re


def sanitise_name_search_query(query: str) -> str | None:
    """
    Sanitise a query string for use with SQLite FTS5.

    Allows FTS5 operators (AND, OR, NOT, NEAR), quoted phrases, and prefix matching.
    Strips column specifiers and boost operators which aren't applicable.
    Returns None if the query is empty after sanitisation.
    """

    if not query or not query.strip():
        return None

    # Strip column specifier (:) and boost (^) - not applicable to our schema
    sanitised = re.sub(r'[:^]', '', query)

    # Balance quotes - unmatched quotes cause FTS syntax errors
    quote_count = sanitised.count('"')
    if quote_count % 2 != 0:
        last_quote = sanitised.rfind('"')
        sanitised = sanitised[:last_quote] + sanitised[last_quote + 1 :]

    return sanitised.strip() or None
