from django.contrib import admin

from network.models import *


admin.site.register(User)
admin.site.register(Follower)
admin.site.register(Post)
admin.site.register(Like)
admin.site.register(Comment)