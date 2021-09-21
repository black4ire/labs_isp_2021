from django.db.models import fields
from django.forms.models import ModelForm
from django.contrib.auth.models import User

from .models import Post

class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text', 'pic')
