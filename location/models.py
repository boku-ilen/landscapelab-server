from enum import Enum

from django.contrib.gis.db import models


# represents a disclosed area with an individual setup of available geodata
class Scenario(models.Model):

    # the name of the project area
    name = models.TextField()

    # the bounding polygon
    bounding_polygon = models.MultiPolygonField()  # TODO: set the default srid (ETRS89-LAEA?)


# an enumeration of all available services which are available for a scenario
class ServiceChoice(Enum):

    DHM = "Digital Height Model"
    ORTHO = "Orthophotos"
    BLDGS = "Buildings"
    TREES = "Trees / Forests"
    # TODO: add more..


# a service which is associated with an scenario
class Service(models.Model):

    # the associated scenario
    scenario = models.ForeignKey(Scenario, related_name='services', on_delete=models.PROTECT)

    # the service identifier
    identifier = models.CharField(max_length=5, choices=[(tag, tag.value) for tag in ServiceChoice])


# a key/value class which provides parameters for a service
class ServiceProperty(models.Model):

    # the associated service
    service = models.ForeignKey(Service, related_name="properties", on_delete=models.PROTECT)

    # the identifier (key) of the property
    key = models.TextField()

    # the value of the property (represented as text)
    value = models.TextField()


# this defines the starting location and alternate interesting visiting points
class Location(models.Model):

    # the description of the location/poi
    name = models.TextField()

    # the geographic coordinates of the location
    location = models.PointField()

    # the direction in which the user should look in the beginning (0 = north)
    direction = models.FloatField()

    # the associated scenario
    scenario = models.ForeignKey(Scenario, related_name="locations", on_delete=models.PROTECT)

    # the order (where the first element defines the starting location for the scenario)
    order = models.IntegerField()

    class Meta:
        ordering = ['order']  # default order by property 'order'


# the associated printed map for the workshops
class Map(models.Model):

    # the associated scenario for this (printed) map
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT)

    # the unique identifier of the printed map
    identifier = models.TextField()

    # define the area which is printed on the workshop handouts
    bounding_box = models.PolygonField()


# represents a single planning session which is to be monitored
# TODO: the current model is just a proposal
class Session(models.Model):

    # automatically fill the timestamp when the recording of a session starts
    starttime = models.DateTimeField(auto_now_add=True)

    # the timestamp when the session changes or the program is terminated (?)
    endtime = models.DateTimeField(null=True, default=None, blank=True)

    # the associated area/location
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT)


# a single notification about the location and viewport of the user
class Impression(models.Model):

    # the associated session
    session = models.ForeignKey(Session, on_delete=models.PROTECT)

    # the location of the camera (3d)
    location = models.PointField(dim=3)

    # the direction of the camera (3d)
    viewport = models.PointField(dim=3)

    # the timestamp the impression is recorded
    timestamp = models.DateTimeField(auto_now_add=True)

    # TODO: how to record the zoom? (either per parameter or as the distance of location to viewport?
