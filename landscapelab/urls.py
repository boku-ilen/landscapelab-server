from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('assetpos/', include('assetpos.urls')),
    path('buildings/', include("buildings.urls")),
    path('location/', include("location.urls")),
    path('raster/', include("raster.urls")),
]
