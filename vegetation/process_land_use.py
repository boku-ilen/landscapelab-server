from PIL import Image

LAND_USE_PIXELS_PER_METER = 0.2
SPLATMAP_PIXELS_PER_METER = 0.2

# Maps land use color to phytocoenosis ID - TODO: This one works for 1:1 mappings, will be replaced!
land_use_color_phytocoenosis_id = {
    (118, 208, 128, 255): 1
}


def land_use_to_splatmap(path_to_land_use):
    """Takes a path to a land use map and constructs and returns a phytocoenosis ID splatmap for it, as well as a set
    with all IDs in this splatmap.
    """

    # Load land use map
    land_use_image = Image.open(path_to_land_use)
    land_use_width_pixels, land_use_height_pixels = land_use_image.size
    land_use_width_meters, land_use_height_meters = land_use_width_pixels / LAND_USE_PIXELS_PER_METER, \
        land_use_height_pixels / LAND_USE_PIXELS_PER_METER
    land_use_pixels = land_use_image.load()

    splatmap_width_pixels, splatmap_height_pixels = int(land_use_width_meters * SPLATMAP_PIXELS_PER_METER), \
        int(land_use_height_meters * SPLATMAP_PIXELS_PER_METER)

    # Create splatmap
    splatmap_image = Image.new('RGB', (splatmap_width_pixels, splatmap_height_pixels))
    splatmap_pixels = splatmap_image.load()

    ids_in_splatmap = set()

    # Go through each pixel on the splatmap
    for x in range(splatmap_width_pixels):
        for y in range(splatmap_height_pixels):
            land_use_x, land_use_y = splatmap_to_land_use_coords(x, y)
            land_use_pixel = land_use_pixels[land_use_x, land_use_y]

            # Map the pixel to the corresponding phytocoenosis ID - TODO: Replace with more sophisticated method
            splat_id = get_splatmap_pixel_for_land_use_pixel(land_use_pixel)
            splatmap_pixels[x, y] = (splat_id, 0, 0)  # TODO: Split the value up to all channels

            # Add this ID to the set of IDs in the map
            ids_in_splatmap.add(splat_id)

    ids_in_splatmap.remove(0)  # Remove the 0 because it just means 'empty' - it is not an ID

    return splatmap_image, ids_in_splatmap


def get_splatmap_pixel_for_land_use_pixel(land_use_pixel):
    """Takes a splatmap pixel and returns the corresponding land_use_pixel.

    If the value is present in the land use color to phytocoenosis ID map, the correct phytocoenosis ID is entered.
    Otherwise, the returned splatmap pixel is 0, meaning no phytocoenosis is present there.

    Currently a 1:1-mapping without using additional parameters - this function will probably be replaced once the
    mapping becomes more sophisticated.
    """

    splatmap_pixel = 0

    if land_use_pixel in land_use_color_phytocoenosis_id:
        splatmap_pixel = land_use_color_phytocoenosis_id[land_use_pixel]

    return splatmap_pixel


def splatmap_to_land_use_pixel(coord):
    """Translates a splatmap pixel coordinate to the corresponding land use pixel coordinate."""

    meter_coord = coord / SPLATMAP_PIXELS_PER_METER
    return meter_coord * LAND_USE_PIXELS_PER_METER


def splatmap_to_land_use_coords(x, y):
    """Translates splatmap x and y pixel coordinates to the corresponding land use x and y pixel coordinates."""

    return splatmap_to_land_use_pixel(x), splatmap_to_land_use_pixel(y)
