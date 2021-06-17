from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = RichTextUploadingField()
    create_time = models.DateTimeField()
    update_time = models.DateTimeField()

    def create(self):
        self.create_time = timezone.now()
        self.save()

    def __str__(self):
        return self.title


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = '__all__'
        exclude = ['user', 'create_time', 'update_time']