import geemap
from ee.image import Image


def image_to_html(
    image: Image,
    name: str = "",
    vis_params: dict = {},
    center: bool = False,
) -> str:
    """Converts an Earth Engine image to an HTML string."""
    demographic_map = geemap.Map()
    demographic_map.add_layer(image, vis_params, name)
    if center:
        demographic_map.center_object(image)
    html = demographic_map.to_html()
    if html is None:
        error_msg = "Failed to generate map"
        raise ValueError(error_msg)

    return html
