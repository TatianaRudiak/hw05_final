from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html

from .models import Comment, Follow, Group, Post

User = get_user_model()


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group', 'image_tag')
    readonly_fields = ('image_tag', 'pub_date', )
    fields = ('text', 'pub_date', 'author', 'group', 'image', 'image_tag')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'

    def image_tag(self, instance):
        if instance.image:
            return format_html(
                '<img src="{0}" style="max-width: 100%"/>',
                instance.image.url
            )


class GroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'slug', 'description')
    search_fields = ('title',)
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    list_filter = ('user', 'author')


class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'post', 'text', 'created', 'author')
    search_fields = ('text',)
    list_filter = ('created',)


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Comment, CommentAdmin)
