from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^(?P<position_x>(\d+(?:\.\d+)))/(?P<position_y>(\d+(?:\.\d+)))/(?P<line_type_id>(\d+)).json$',
        views.get_lines_near_position, name="get_lines_near_position"),

    url(r'^tile/(?P<line_type_id>(\d+))/(?P<tile_x>(\d+(?:\.\d+)))/(?P<tile_y>(\d+(?:\.\d+)))/(?P<zoom>(\d+)).json$',
        views.get_lines_for_tile, name="get_lines_for_tile")

]
