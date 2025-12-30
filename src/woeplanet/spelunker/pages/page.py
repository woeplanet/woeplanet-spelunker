"""
WOEplanet Spelunker: common package; render helpers module.
"""

from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.config.place_scale import placetype_to_scale
from woeplanet.spelunker.dependencies.templates import get_templater
from woeplanet.spelunker.pages.random import _random_place

TemplateArg = str | int | float | bool | list | dict | None


async def render_page(
    request: Request,
    template_name: str,
    title: str,
    **extra_args: TemplateArg,
) -> HTMLResponse:
    """
    Render a static page with a random place background.
    """

    place = await _random_place(request=request)
    template = get_templater().get_template(template_name)
    template_args = {
        'map': True,
        'centroid': place.get('centroid'),
        'bounds': place.get('bounds'),
        'title': title,
        'woeid': place.get('woe_id'),
        'iso': place.get('iso', 'GB'),
        'nearby': place.get('woe_id'),
        'name': place.get('name'),
        'scale': placetype_to_scale(int(place.get('placetype_id', 0))),
        'doc': place,
        **extra_args,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content)
