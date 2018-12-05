from django.contrib.gis.db import models


# represents a disclosed area with an individual setup of available geodata
class Scenario(models.Model):

    # the name of the project area
    name = models.TextField()

    # start location when first entering the scenario
    start_location = models.PointField()

    # the bounding polygon (TODO: is a seperate bounding box necessairy?)
    bounding_polygon = models.MultiPolygonField()  # TODO: set the default srid (ETRS89-LAEA?)


# FIXME: how to tell the client which service layers are available in this scenario or on this specific location
# class Services(models.Model):


# represents a single planning session which is to be monitored
# TODO: the current model is just a proposal
class Session(models.Model):

    # automatically fill the timestamp when the recording of a session starts
    starttime = models.DateTimeField(auto_now_add=True)

    # the timestamp when the session changes or the program is terminated (?)
    endtime = models.DateTimeField(null=True, default=None, blank=True)

    # the workshop identifier of the recording
    workshop = models.TextField(null=True, default=None, blank=True)

    # the associated area/location
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT)


# a single notification about the location and viewport of the user
class Impression(models.Model):

    # the associated session
    session = models.ForeignKey(Session, on_delete=models.PROTECT)

    # the location of the camera (3d)
    location = models.PointField()

    # the direction of the camera (3d)
    viewport = models.PointField()

    # the timestamp the impression is recorded
    timestamp = models.DateTimeField(auto_now_add=True)

    # TODO: how to record the zoom? (either per parameter or as the distance of location to viewport?
