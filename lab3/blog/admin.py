from django.contrib import admin
from .models import AdditionalUserFeatures, Category, Post

admin.site.register(Post)
admin.site.register(AdditionalUserFeatures)
admin.site.register(Category)