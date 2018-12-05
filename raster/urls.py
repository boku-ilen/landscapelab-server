from django.conf.urls import url

from . import views

urlpatterns = [

    # deliver a static raster image by given filename
    url(r'^(?P<filename>[\w,\s-]+\.[A-Za-z]{2,4})$', views.static_raster, name="static_raster"),
]
