from django.contrib.gis.db import models


# represents a single planning session which is to be monitored
# TODO: the current model is just a proposal
class Session(models.Model):

    # automatically fill the timestamp when the recording of a session starts
    starttime = models.DateTimeField(auto_now_add=True)

    # the timestamp when the session changes or the program is terminated (?)
    endtime = models.DateTimeField(null=True, default=None, blank=True)

    # the workshop identifier of the recording
    workshop = models.TextField(null=True, default=None, blank=True)

    # the area/location
    # TODO: maybe change it to a reference to a instance of a model for each area
    area = models.TextField(null=True, default=None, blank=True)


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

    # TODO: how to record the zoom? (eigther per parameter or as the distance of location to viewport?
