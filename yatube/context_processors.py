from posts.models import Group, Post

from django.contrib.auth import get_user_model


def total_counters(request):
    posts_total_count = Post.objects.count()
    groups_total_count = Group.objects.count()
    authors_total_count = get_user_model().objects.exclude(posts=None).count()
    return {
        'posts_total_count': posts_total_count,
        'groups_total_count': groups_total_count,
        'authors_total_count': authors_total_count,
    }
