import logging
import datetime

from django.contrib.gis.geos import Point
from pysolar import solar
from django.http import JsonResponse, HttpResponse

from location.models import Impression, Scenario, Session, Map


logger = logging.getLogger(__name__)


# uses the pysolar library to calculate the sun angles of a given time and location
def sunposition(request, year, month, day, hour, minute, lat, long, elevation):

    # do some sanity checks
    # TODO: ...

    # perform the calculation via pysolar
    # FIXME: what to do with the timezone? (make it configurable in the settings or selectable in the client?)
    date = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), 0, 0, tzinfo=datetime.timezone.utc)
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
    # FIXME: how to handle srid/projection (?)
    try:
        impression.location = Point(float(x), float(y), float(elevation))
        impression.viewport = Point(float(target_x), float(target_y), float(target_elevation))
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
                'location': (location.x, location.y),
                'direction': location.direction,
                'starting_location': first,
            }
            first = False

        # return the scenario as json
        result[entry.pk] = {'name': entry.name,
                            'locations': locations,
                            'bounding_polygon': entry.bounding_polygon.json}
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
        'bounding_box': printed_map.bounding_box
    }

    return JsonResponse(result)
