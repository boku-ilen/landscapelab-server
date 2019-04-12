from django.conf.urls import url

from . import views

urlpatterns = [

    # deliver the phytocoenosis splatmap for a given position
    url(r'^(?P<meter_x>(\d+(?:\.\d+)))/(?P<meter_y>(\d+(?:\.\d+)))/(?P<zoom>(\d+))',
        views.get_vegetation_splatmap, name="get_vegetation_splatmap"),

    # deliver the required data for a phytocoenosis in a given layer
    url(r'^(?P<phyto_c_id>(\d+))/(?P<layer_name>(.*))',
        views.get_phytocoenosis_data, name="get_phytocoenosis_data")

]
