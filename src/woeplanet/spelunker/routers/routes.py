"""
WOEplanet Spelunker: routers package; routes module.
"""

from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from woeplanet.spelunker.config.settings import get_settings
from woeplanet.spelunker.pages.about import about_endpoint
from woeplanet.spelunker.pages.countries import countries_endpoint, country_endpoint
from woeplanet.spelunker.pages.credits import credits_endpoint
from woeplanet.spelunker.pages.index import index_endpoint
from woeplanet.spelunker.pages.licenses import licenses_endpoint
from woeplanet.spelunker.pages.nullisland import nullisland_endpoint
from woeplanet.spelunker.pages.places import nearby_endpoint, place_endpoint, place_map_endpoint, place_nearby_endpoint
from woeplanet.spelunker.pages.placetypes import placetype_facets_endpoint, placetype_search_endpoint
from woeplanet.spelunker.pages.random import random_endpoint
from woeplanet.spelunker.pages.search import search_endpoint

settings = get_settings()


def routes() -> list[Route | Mount]:
    """
    Return all routes and their handlers
    """

    return [
        Route(path='/', endpoint=index_endpoint),
        Route(path='/about', endpoint=about_endpoint),
        Route(path='/credits', endpoint=credits_endpoint),
        Route(path='/countries', endpoint=countries_endpoint),
        Route(path='/countries/{iso:str}', endpoint=country_endpoint),
        Route(path='/id/{woeid:int}', endpoint=place_endpoint),
        Route(path='/id/{woeid:int}/map', endpoint=place_map_endpoint),
        Route(path='/id/{woeid:int}/nearby', endpoint=place_nearby_endpoint),
        Route(path='/nearby', endpoint=nearby_endpoint),
        Route(path='/nullisland', endpoint=nullisland_endpoint),
        Route(path='/placetypes', endpoint=placetype_facets_endpoint),
        Route(path='/placetypes/{placetype:str}', endpoint=placetype_search_endpoint),
        Route(path='/random', endpoint=random_endpoint),
        Route(path='/search', endpoint=search_endpoint),
        Route(path='/licenses', endpoint=licenses_endpoint),
        Mount(path='/static', app=StaticFiles(directory=settings.static_dir), name='static'),
    ]
