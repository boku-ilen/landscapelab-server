import json
import logging
import datetime
import os
from json import JSONDecodeError

from django.contrib.gis.geos import Point, MultiPolygon
from django.contrib.staticfiles import finders
from pysolar.solar import get_altitude, get_azimuth
from django.http import JsonResponse, HttpResponse

from location.models import Impression, Scenario, Session

logger = logging.getLogger("MainLogger")


# uses the pysolar library to calculate the sun angles of a given time and location
def sunposition(request, year, month, day, hour, minute, lat, long, elevation):

    # do some sanity checks
    # TODO: ...

    # perform the calculation via pysolar
    # FIXME: what to do with the timezone? (make it configurable in the settings or selectable in the client?)
    date = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), 0, 0, tzinfo=datetime.timezone.utc)
    azimuth = get_azimuth(float(lat), float(long), date, float(elevation))
    altitude = get_altitude(float(lat), float(long), date, float(elevation))

    # construct the answer
    result = {
        'azimuth': azimuth,
        'altitude': altitude,
    }
    return JsonResponse(result)


# registers an impression into the database
def register_impression(request, x, y, elevation, target_x, target_y, target_elevation, session_id):

    # TODO: maybe add some sanity checks

    # create a new impression object with the given parameters and stores it in the database
    # FIXME: how to figure out the associated session object? (store it in the HTTP session?)

    try:
        session = Session.objects.get(pk=session_id)
    except Session.DoesNotExist:
        logger.error("Unknown session Id")
        return HttpResponse(status=404)

    impression = Impression()
    impression.session = session
    # FIXME: how to handle srid/projection (?)
    impression.location = Point(float(x), float(y), float(elevation))
    impression.viewport = Point(float(target_x), float(target_y), float(target_elevation))
    impression.save()

    # return an empty content http response
    return HttpResponse(status=204)


# results an unfiltered list of all configured project on this server
def project_list(request):
    result = Scenario.objects.all()
    return JsonResponse(result)  # FIXME: does this correctly convert to json?


# currently we just deliver the preconfigured json.
# TODO: in the future get the dynamic list of available services for the database
def services_list(request):
    if 'filename' not in request.GET:
        path = finders.find("areas")
        area_files = os.listdir(path)
        area_list = []
        for area in area_files:
            if os.path.splitext(area)[1] == '.json':
                area_list.append(os.path.splitext(area)[0])
        return JsonResponse({"Areas": area_list})
    filename = request.GET.get('filename')

    path = finders.find(os.path.join("areas", filename + ".json"))
    logger.debug("delivering area with filename {}".format(path))

    if path is None:
        return JsonResponse({"Error": "file does not exist"})

    try:
        with open(path) as f:
            data = json.load(f)
        return JsonResponse(data)
    except JSONDecodeError:
        return JsonResponse({"Error": "invalid JSON data"})


#
def create_session(request, area):
    # logger.debug("area is %s" % str(area))

    s = Session()
    try:
        logger.info("Loading scenario %s" % area)
        scenario = Scenario.objects.get(name=area)
    except Scenario.DoesNotExist:
        # TODO return error instead
        logger.debug("Scenario %s unknown creating new scenario" % area)
        scenario = Scenario(name=area)
        scenario.start_location = Point(0, 0)
        scenario.bounding_polygon = MultiPolygon()
        scenario.save()
    s.scenario = scenario
    s.save()

    return JsonResponse({'Data': s.pk})
