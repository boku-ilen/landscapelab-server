from django.conf.urls import url

from . import views

urlpatterns = [

    # deliver a static raster image by given filename
    url(r'^(?P<filename>[\w,\s-]+\.[A-Za-z]{2,4})$', views.static_raster, name="static_raster"),

    # get the filename of a pyramid tile based on meter data
    # this also triggers the on-demand calculation of the required
    # height data and splatmaps - will return an according json
    url(r'^(?P<meter_x>(\d+(?:\.\d+)))/(?P<meter_y>(\d+(?:\.\d+)))/(?P<zoom>(\d+)).json$',
        views.get_ortho_dhm, name="get_ortho_and_dhm")

]
