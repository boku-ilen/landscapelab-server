from django.conf.urls import url

from . import views

urlpatterns = [

    # deliver a static raster image by given filename
    url(r'^(?P<filename>[\w,\s-]+\.[A-Za-z]{2,4})$', views.static_raster, name="static_raster"),

    # deliver the old dhm format  TODO: change API
    url(r'^dhm', views.get_dhm, name="get_dhm"),

    # get the filename of an combined ortho + heightmap based on meter data
    #TODO: do we want to deliver it in json or just as plain txt
    url(r'/(?P<layer>\s)/(?P<meter_x>(\d+(?:\.\d+)))/(?P<meter_y>(\d+(?:\.\d+)))/(?P<zoom(\d+)).json$',
        views.filename_from_coords, name="filename_from_coords")

]
