

# FIXME: Maybe move to views?
def can_place_at_position(assettype, meter_x, meter_y):
    """Returns true if the asset with the given id may be placed at the given position."""

    placement_areas = assettype.placement_areas

    # if there are no placement areas present it is not allowed
    # to place an asset of this asset type
    if not placement_areas:
        return False

    # TODO: Implement using polygons which define areas that are allowed
    return True
