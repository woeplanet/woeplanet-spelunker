"""
WOEplanet Spelunker: pages package; data page module
"""

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse

from woeplanet.spelunker.config.manifest import get_manifest
from woeplanet.spelunker.config.place_scale import placetype_to_scale
from woeplanet.spelunker.config.settings import get_settings
from woeplanet.spelunker.dependencies.templates import get_templater
from woeplanet.spelunker.pages.random import _random_place


async def data_endpoint(request: Request) -> HTMLResponse:
    """
    Data page endpoint
    """

    place = await _random_place(request=request)
    manifest = get_manifest()

    template = get_templater().get_template('data.html.j2')
    template_args = {
        'map': True,
        'centroid': place.get('centroid'),
        'bounds': place.get('bounds'),
        'title': 'Data',
        'woeid': place.get('woe_id'),
        'name': place.get('name'),
        'scale': placetype_to_scale(int(place.get('placetype_id', 0))),
        'doc': place,
        'manifest': manifest,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content)


async def download_endpoint(request: Request) -> FileResponse:
    """
    Download file endpoint
    """

    settings = get_settings()
    filename = request.path_params['filename']
    file_path = settings.woeplanet_downloads_dir / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail='File not found')

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream',
    )
