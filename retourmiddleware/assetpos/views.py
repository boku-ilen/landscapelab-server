from django.http import JsonResponse
import os.path
# from .shp_reader import *
from .shp_to_json import get_trees
from .util import *
import json

# from osgeo import gdal
from osgeo import ogr


# Create your views here.
def index(request):
    if 'filename' not in request.GET:
        return JsonResponse({"Error": "no filename specified"})
    filename = request.GET.get('filename')
    BASE = os.path.dirname(os.path.abspath(__file__))
    gen_file_path = os.path.join(BASE, "generatedFiles", filename + ".json")
    file_path = os.path.join(BASE, "inputFiles", filename + ".shp")
    recalculate = str_to_bool(request.GET.get('recalc')) if 'recalc' in request.GET else False

    if os.path.isfile(gen_file_path) and not recalculate:
        print("opening ", gen_file_path)

        with open(gen_file_path) as f:
            data = json.load(f)
        return JsonResponse(data)
    elif os.path.isfile(file_path):
        print("opening %s" % file_path)

        driver = ogr.GetDriverByName('ESRI Shapefile')
        if driver is None:
            return JsonResponse({"Error": "driver not available ESRI Shapefile"})

        data_set = driver.Open(file_path, 0)

        if data_set is None:
            return JsonResponse({"Error": "could not open " + file_path})
        else:
            print("opened %s" % file_path)
            data = get_trees(data_set, request)

            print("saving data to file")
            with open(gen_file_path, 'w') as outfile:
                json.dump(data, outfile)

            print("returning json")
            # return JsonResponse(data, json_dumps_params={'indent': 2})
            return JsonResponse(data)
    else:
        return JsonResponse({"Error": "file %s.shp does not exist" % filename})
