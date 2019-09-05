from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include

from landscapelab import utils

urlpatterns = [
    path('admin/', admin.site.urls),
    path('assetpos/', include('assetpos.urls')),
    path('buildings/', include('buildings.urls')),
    path('location/', include('location.urls')),
    path('raster/', include('raster.urls')),
    path('vegetation/', include('vegetation.urls')),
    path('linear/', include('linear.urls')),
    path('energy/', include('energy.urls')),
    url(r'^reload_logging', utils.reload_logging),
]
