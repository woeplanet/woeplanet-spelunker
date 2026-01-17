"""
WOEplanet Spelunker: dependencies package; templates module.
"""

from functools import lru_cache
from http import HTTPStatus

import emoji
import inflect
import jinja2
import pyuca
from starlette.templating import Jinja2Templates

from woeplanet.spelunker.common.languages import language_name
from woeplanet.spelunker.config.settings import get_settings

NAME_TYPES = {
    'S': 'standard',
    'P': 'preferred',
    'V': 'variant',
    'Q': 'colloquial',
    'A': 'abbreviated',
}

settings = get_settings()
collator = pyuca.Collator()
inflect_engine = inflect.engine()


def plural_filter(value: str, count: int | None = None) -> str:
    """
    Jinja filter; returns the plural of a word or phrase

    e.g. "Point of Interest" -> "Points of Interest"
    """

    if not value:
        return value

    return inflect_engine.plural(value, count)


def any_filter(value: str) -> str:
    """
    Jinja filter; a vs. an
    """

    if value.lower() == 'miscellaneous':
        return value
    return inflect_engine.an(value)


def language_filter(value: str) -> str:
    """
    Jinja filter; returns the language name for an ISO 639 code
    """

    return language_name(value)


def unicode_sort_filter(value: list, attribute: str | None = None) -> list:
    """
    Jinja filter; sorts using Unicode Collation Algorithm
    """

    if attribute:
        return sorted(value, key=lambda x: collator.sort_key(x.get(attribute, '')))

    return sorted(value, key=collator.sort_key)


def http_phrase_filter(value: int) -> str:
    """
    Jinja filter; returns the HTTP phrase for a status code
    """

    return HTTPStatus(value).phrase


def http_description_filter(value: int) -> str:
    """
    Jinja filter; returns the HTTP description for a status code
    """

    return HTTPStatus(value).description


def comma_filter(value: int) -> str:
    """
    Jinja filter; returns the value as hundreds, thousands, etc formatted string
    """

    return f'{value:,}'


def name_type_filter(value: str) -> str:
    """
    Jinja filter; returns the name type description for a code
    """

    return NAME_TYPES.get(value, 'unknown')


def emoji_filter(value: str) -> str:
    """
    Jinja2 filter; returns a CLDR short form emoji
    """

    return emoji.emojize(f':{value}:', language='alias')


@lru_cache
def get_templater() -> Jinja2Templates:
    """
    Return the Jinja2 templates instance including custom filters
    """

    loader = jinja2.FileSystemLoader(str(settings.woeplanet_templates_dir))
    env = jinja2.Environment(autoescape=True, enable_async=True, loader=loader)

    env.filters['langname'] = language_filter
    env.filters['pluralise'] = plural_filter
    env.filters['unicode_sort'] = unicode_sort_filter
    env.filters['http_phrase'] = http_phrase_filter
    env.filters['http_description'] = http_description_filter
    env.filters['commafy'] = comma_filter
    env.filters['anyfy'] = any_filter
    env.filters['name_type'] = name_type_filter
    env.filters['emojify'] = emoji_filter

    return Jinja2Templates(env=env)
