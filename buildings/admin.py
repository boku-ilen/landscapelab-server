from django.contrib import admin
from .models import BuildingLayout
from django.contrib.gis.db import models
from .forms import LatLongWidget

class BuildingLayoutAdmin(admin.ModelAdmin):
    list_display = ['asset']
    fields = ['asset', 'vertices']
    formfield_overrides = {
        models.PointField: {'widget': LatLongWidget}
    }

# Register your models here.
admin.site.register(BuildingLayout, BuildingLayoutAdmin)