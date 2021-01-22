from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


def paginate(request, qs, limit):
    paginator = Paginator(qs, limit)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def construct_search(q):
    if q.startswith('^'):
        return 'text__istartswith', q[1:]
    elif q.startswith('='):
        return 'text__iexact', q[1:]
    elif q.startswith('@') or q.startswith('#'):
        return q.split()[0], ''.join(q.split()[1:])
    else:
        return ['text__icontains', q]


def search_results(request):
    q = request.GET['q']
    if not q:
        return redirect(request.META.get('HTTP_REFERER', reverse('posts:index')))
    q_search, q_cleaned = construct_search(str(q))
    msg_q = f'"{q_cleaned}"'
    results = []
    if q_search.startswith('@'):
        try:
            author = User.objects.get(username=q_search[1:])
            results = Post.objects.filter(author=author).filter(Q(text__icontains=q_cleaned))
            msg_q += f' в постах автора: {q_search}'
        except Exception:
            msg_q = f'Не найден автор: {q_search}'
    elif q_search.startswith('#'):
        try:
            group = Group.objects.get(slug=q_search[1:])
            results = Post.objects.filter(group=group).filter(Q(text__icontains=q_cleaned))
            msg_q += f' в постах из группы: {q_search}'
        except Exception:
            msg_q = f'Не найдена группа: {q_search}'
    else:
        results = Post.objects.filter(Q(**{q_search: q_cleaned}))
    page = paginate(request, results, 10)
    return render(request, 'posts/search_results.html', {'page': page, 'q': q, 'msg_q': msg_q, })


@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    if form.is_valid():
        form.instance.author = request.user
        form.instance.post = post
        form.save()
        return redirect(reverse('posts:post',  kwargs={'username': username, 'post_id': post_id})+'#all_comments')
    return redirect(reverse('posts:post',  kwargs={'username': username, 'post_id': post_id})+'#add_comment')


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        form.instance.author = request.user
        form.save()
        return redirect(reverse('posts:index'))
    return render(request, 'posts/new_post.html', {'form': form})


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('group').all()
    page = paginate(request, post_list, 10)
    return render(request, 'posts/index.html', {'page': page, 'paginator': page.paginator, })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page = paginate(request, post_list, 10)
    return render(request, 'posts/group.html', {'group': group, 'page': page, 'paginator': page.paginator, })


def groups(request):
    group_list = Group.objects.all().order_by('pk')
    page = paginate(request, group_list, 10)
    return render(request, 'posts/groups.html', {'page': page, 'paginator': page.paginator, })


def users(request):
    user_list = User.objects.all().order_by('pk')
    following = request.user.is_authenticated and User.objects.filter(following__user=request.user)
    page = paginate(request, user_list, 12)
    return render(request, 'posts/users.html', {
        'page': page,
        'following': following,
        'paginator': page.paginator,
    })


@login_required
def followees(request):
    user_list = User.objects.filter(following__user=request.user).order_by('pk')
    page = paginate(request, user_list, 12)
    return render(request, 'posts/followees.html', {'page': page, 'paginator': page.paginator, })


@login_required
def followers(request):
    user_list = User.objects.filter(follower__author=request.user).order_by('pk')
    following = User.objects.filter(following__user=request.user)
    page = paginate(request, user_list, 12)
    return render(request, 'posts/followers.html', {
        'page': page,
        'paginator': page.paginator,
        'following': following,
    })


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    post_list = profile_user.posts.all()
    page = paginate(request, post_list, 10)
    following = request.user.is_authenticated and User.objects.filter(
        following__user=request.user,
        following__author=profile_user
    )
    return render(request, 'posts/profile.html', {
            'profile_user': profile_user,
            'page': page,
            'paginator': page.paginator,
            'following': following,
        })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    form = CommentForm(request.POST or None)
    following = request.user.is_authenticated and User.objects.filter(
        following__user=request.user,
        following__author__username=username,)
    return render(request, 'posts/post.html', {'post': post, 'form': form, 'following': following,})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    if post.author != request.user:
        return redirect(reverse('posts:post', kwargs={'username': username, 'post_id': post_id}))
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect(reverse('posts:post', kwargs={'username': username, 'post_id': post_id}))
    return render(request, 'posts/new_post.html', {'form': form, 'post': post})


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page = paginate(request, post_list, 10)
    return render(request, 'posts/follow.html', {'page': page, 'paginator': page.paginator, })


@login_required
def profile_follow(request, username):
    profile_user = get_object_or_404(User, username=username)
    if request.user != profile_user:
        Follow.objects.get_or_create(user=request.user, author=profile_user)
    return redirect(request.META.get('HTTP_REFERER', reverse('posts:profile', kwargs={'username': username})))


@login_required
def profile_unfollow(request, username):
    follow = Follow.objects.filter(user=request.user, author__username=username)
    follow.delete()
    return redirect(request.META.get('HTTP_REFERER', reverse('posts:profile', kwargs={'username': username})))


def page_not_found(request, exception=None):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)
