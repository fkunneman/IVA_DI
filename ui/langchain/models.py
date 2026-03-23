from django.db import models


class Session(models.Model):
    model = models.CharField(max_length=255, )
