import logging
import datetime

from django.contrib.gis import geos
from django.contrib.gis.geos import Point
from pysolar import solar
from django.http import JsonResponse, HttpResponse

from energy.views import get_energy_targets
from location.models import Impression, Scenario, Session, Map, Location

logger = logging.getLogger(__name__)

WEBMERCATOR_SRID = 3857


# uses the pysolar library to calculate the sun angles of a given time and location
def sunposition(request, year, month, day, hour, minute, lat, long, elevation):
    # do some sanity checks
    # TODO: ...

    # perform the calculation via pysolar
    # FIXME: what to do with the timezone? (make it configurable in the settings or selectable in the client?)
    date = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), 0, 0,
                             tzinfo=datetime.timezone.utc)
    azimuth = solar.get_azimuth(float(lat), float(long), date, float(elevation))
    altitude = solar.get_altitude(float(lat), float(long), date, float(elevation))

    # construct the answer
    result = {
        'azimuth': azimuth,
        'altitude': altitude,
    }
    return JsonResponse(result)


# registers an impression into the database
def register_impression(request, x, y, elevation, target_x, target_y, target_elevation, session_id):
    try:
        session = Session.objects.get(pk=session_id)
    # the associated session could not be found - we drop the impression
    except Session.DoesNotExist:
        logger.error("unknown session ID {}".format(session_id))
        return HttpResponse(status=404)

    # create a new impression object with the given parameters and stores it in the database
    impression = Impression()
    impression.session = session

    try:
        # the client always uses webmercator coordinates, so we specify the srid
        impression.location = Point(float(x), float(y), float(elevation), srid=WEBMERCATOR_SRID)
        impression.viewport = Point(float(target_x), float(target_y), float(target_elevation), srid=WEBMERCATOR_SRID)
        impression.save()
        logger.debug("stored impression {}".format(impression))
    except ValueError:
        logger.error("invalid parameters to register_impression: {} {} {} {} {} {}".format(x, y, elevation, target_x,
                                                                                           target_y, target_elevation))
        return HttpResponse(status=500)

    # return an empty content http response
    return HttpResponse(status=204)


# results an unfiltered list of all configured scenarios on this server
def scenario_list(request):
    result = {}
    lst = Scenario.objects.all()
    for entry in lst:

        # prepare locations and flag the starting location (first entry in order)
        locations = {}
        first = True
        for location in entry.locations.all():
            locations[location.order] = {
                'name': location.name,
                'location': (location.location.x, location.location.y),
                'direction': location.direction,
                'starting_location': first,
            }
            first = False

        # return the scenario as json
        result[entry.pk] = {'name': entry.name,
                            'locations': locations,
                            'bounding_polygon': entry.bounding_polygon.json,
                            'energy_requirement_total': get_energy_targets(entry.pk),  # use the energy module
                            'default_wind_direction': entry.default_wind_direction}

    return JsonResponse(result)


# get the dynamic configuration of a scenario
def services_list(request, scenario_id):
    services = {}
    scenario = Scenario.objects.get(scenario_id)
    for service in scenario.services:
        services[service.identifier] = {}
        for ppty in service.properties:
            services[service.identifier][ppty.key] = ppty.value
    return JsonResponse(services)


# we start a new tracking session for a given scenario
def start_session(request, scenario_id):
    session = Session()
    try:
        scenario = Scenario.objects.get(pk=scenario_id)
    # the associated scenario could not be found - we return an error
    except Scenario.DoesNotExist:
        logger.warning("could not find associated scenario with id {}".format(scenario_id))
        return HttpResponse(status=404)

    session.scenario = scenario
    session.save()
    logger.info("created session {} for scenario {}".format(session, scenario))

    return JsonResponse({'session': session.pk})


# returns information like the bounding box of a printed map
# TODO: this is a draft version which has to be adapted to the lego implementation
def get_map(request, map_id):
    # TODO: or do we want to ask for the identifier in workshop model?
    printed_map = Map.objects.get(id=map_id)
    result = {
        'identifier': printed_map.identifier,
        'bounding_box': printed_map.bounding_box.json
    }

    return JsonResponse(result)


def register_location(request, name, meter_x, meter_y, scenario_id):
    """Called when a new location (a.k.a. point of interest) is created at the given x, y.
    Returns a JsonResponse with 'creation_success' (bool) and, if true, the
    'location_id' of the new point of interest."""

    ret = {
        "creation_success": False,
        "location_id": None
    }

    if not Scenario.objects.filter(id=scenario_id):
        logger.warn("Non-existent scenario with ID {} requested!".format(scenario_id))
        return JsonResponse(ret)

    scenario = Scenario.objects.get(id=scenario_id)

    location_point = geos.Point(float(meter_x), float(meter_y))

    lst = Scenario.objects.all()

    highest_order = 0
    for entry in lst:
        for location in entry.locations.all():
            if highest_order < location.order:
                highest_order = location.order

    new_location = Location(name=name, location=location_point, direction=0.0,
                            scenario=scenario, order=highest_order + 10)

    new_location.save()

    ret["creation_success"] = True
    ret["location_id"] = new_location.id

    return JsonResponse(ret)


def remove_location(request, location_name, scenario_id):
    """Called when a location (a.k.a. point of interest) should be deleted.
    Returns a bool indicating if the removal was successful."""

    ret = {
        "removal_success": False
    }

    if not Scenario.objects.filter(id=scenario_id):
        logger.warn("Non-existent scenario with ID {} requested!".format(scenario_id))
        return JsonResponse(ret)

    if not Location.objects.filter(scenario_id=scenario_id, name=location_name).exists():
        logger.warn("Tried to remove a non-existent location (PoI) with name {}" . format(location_name))
        return JsonResponse(ret)

    Location.objects.filter(scenario_id=scenario_id, name=location_name).delete()

    ret["removal_success"] = True

    return JsonResponse(ret)


def increase_location_order(request, location_name):
    """Called when a location's order (a.k.a. point of interest) should be increased.
        Returns a bool indicating if the increase was successful."""

    ret = {
        "order_increased": False,
        "old_order": None,
        "new_order": None
    }

    if not Location.objects.filter(name=location_name).exists():
        logger.warn("Tried to remove a non-existent location (PoI) with name {}".format(location_name))
        return JsonResponse(ret)

    current_location = Location.objects.get(name=location_name)
    lst = Scenario.objects.all()
    swap_location = current_location

    for entry in lst:
        for other_location in entry.locations.filter(scenario_id=10):
            if other_location.order != current_location.order:
                swap_location = other_location
            else:
                break

    temp_order = swap_location.order
    swap_location.order = current_location.order
    current_location.order = temp_order

    swap_location.save()
    current_location.save()

    ret["order_increased"] = True
    ret["old_order"] = swap_location.order
    ret["new_order"] = current_location.order

    return JsonResponse(ret)


def decrease_location_order(request, location_name):
    """Called when a location's order (a.k.a. point of interest) should be decreased.
            Returns a bool indicating if the decrease was successful."""

    ret = {
        "order_decreased": False,
        "old_order": None,
        "new_order": None
    }

    if not Location.objects.filter(name=location_name).exists():
        logger.warn("Tried to remove a non-existent location (PoI) with name {}".format(location_name))
        return JsonResponse(ret)

    current_location = Location.objects.get(name=location_name)
    lst = Scenario.objects.all()
    swap_location = current_location

    for entry in lst:
        for other_location in entry.locations.filter(scenario_id=10).reverse():
            if other_location.order != current_location.order:
                swap_location = other_location
            else:
                break

    temp_order = swap_location.order
    swap_location.order = current_location.order
    current_location.order = temp_order

    swap_location.save()
    current_location.save()

    ret["order_decreased"] = True
    ret["old_order"] = swap_location.order
    ret["new_order"] = current_location.order

    return JsonResponse(ret)

