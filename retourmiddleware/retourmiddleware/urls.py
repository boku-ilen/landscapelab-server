from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('dhm/', include('dhm.urls')),
    path('areas/', include('areas.urls')),
    path('assetpos/', include('assetpos.urls')),
    path('buildings/', include("buildings.urls")),
    path('location/', include("location.urls")),
    path('maps/', include("maps.urls")),
]
