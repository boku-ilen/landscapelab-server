from django.contrib.gis.db import models


# this defines the starting location and alternate interesting visiting points
class Location(models.Model):

    # the description of the location/poi
    name = models.TextField()

    # the geographic coordinates of the location
    location = models.PointField()

    # the direction in which the user should look in the beginning (0 = north)
    direction = models.FloatField()


# represents a disclosed area with an individual setup of available geodata
class Scenario(models.Model):

    # the name of the project area
    name = models.TextField()

    # start location when first entering the scenario
    start_location = models.ForeignKey(Location, on_delete=models.PROTECT)

    # the bounding polygon (TODO: is a seperate bounding box necessairy?)
    bounding_polygon = models.MultiPolygonField()  # TODO: set the default srid (ETRS89-LAEA?)


#
class Map(models.Model):

    # the associated scenario for this (printed) map
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT)

    # the unique identifier of the printed map
    identifier = models.TextField()

    # the timestamp when the workshop takes/took place
    date = models.DateTimeField()

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
