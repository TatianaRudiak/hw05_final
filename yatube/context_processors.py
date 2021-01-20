from django.contrib.auth import get_user_model

from posts.models import Group, Post


def total_counters(request):
    return {
        'posts_total_count': Post.objects.count(),
        'groups_total_count': Group.objects.count(),
        'authors_total_count': get_user_model().objects.count(),
    }
