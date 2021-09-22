from django.conf import settings
from django.db import models
from django.utils import timezone


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='posts', on_delete=models.CASCADE)
    title = models.CharField(max_length=50, unique=True)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)
    pic = models.ImageField(upload_to='blog/%Y/%m/%d', null=True, blank=True)

    class Meta:
        ordering = ['-created_date']

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title

class AdditionalUserFeatures(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='features')
    favourite_post = models.OneToOneField(Post, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.username

class Category(models.Model):
    posts = models.ManyToManyField(Post, related_name='categories', blank=True)
    name = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.name
