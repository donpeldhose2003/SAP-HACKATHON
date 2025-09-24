from django.db import models

class Speaker(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField()
    company = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Session(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    speaker = models.ForeignKey(Speaker, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title