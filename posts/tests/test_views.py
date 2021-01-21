from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client
from django.urls import reverse

from posts.models import Follow, Group, Post
from posts.tests import MyTestCase

User = get_user_model()


class PostsPagesViewsTests(MyTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Текст',
            slug='test-slug'
        )
        cls.user = User.objects.create(username='TestUser')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user,
        )
        cls.posts = cls.group.posts.all()[:11]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsPagesViewsTests.user)
        cache.clear()

    def test_pages_use_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/new_post.html': reverse('posts:new_post'),
            'posts/group.html': (reverse(
                'posts:group-post', kwargs={'slug': PostsPagesViewsTests.group.slug}
            )),
            'posts/post.html': reverse(
                'posts:post',
                kwargs={
                    'username': PostsPagesViewsTests.post.author.username,
                    'post_id': PostsPagesViewsTests.post.pk
                }
            ),
            'posts/profile.html': reverse(
                'posts:profile', kwargs={'username': PostsPagesViewsTests.user.username}
            )
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_group_post_pages_show_correct_context(self):
        """Шаблон group-post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
                reverse('posts:group-post', kwargs={'slug': PostsPagesViewsTests.group.slug})
        )
        self.assert_equal_attr(
            response.context.get('group'),
            PostsPagesViewsTests.group,
            'title', 'description', 'slug'
        )
        self.assert_equal_attr(
            response.context.get('page').object_list[0],
            PostsPagesViewsTests.posts[0],
            'text', 'group', 'author'
        )

    def test_page_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        pages_names_kwargs = {
            'posts:new_post': {},
            'posts:post_edit': {
                'username': PostsPagesViewsTests.post.author.username,
                'post_id': PostsPagesViewsTests.post.pk,
            }
        }
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for page_name, kwargs in pages_names_kwargs.items():
            response = self.authorized_client.get(reverse(page_name, kwargs=kwargs))
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        response_page_0 = response.context.get('page').object_list[0]
        self.assert_equal_attr(response_page_0, PostsPagesViewsTests.post, 'author', 'text', 'group')

    def test_post_page_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post', kwargs={
            'username': PostsPagesViewsTests.post.author,
            'post_id': PostsPagesViewsTests.post.pk
        }))
        post = response.context.get('post')
        self.assert_equal_attr(post, PostsPagesViewsTests.post, 'group', 'text', 'author')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:profile', kwargs={
            'username': PostsPagesViewsTests.user.username
        }))
        self.assert_equal_attr(response.context.get('profile_user'), PostsPagesViewsTests.user)
        self.assert_equal_attr(
            response.context.get('page').object_list[0],
            PostsPagesViewsTests.post,
            'group', 'text', 'author'
        )

    def test_index_page_cached(self):
        """Страница index.html кэшируется"""
        [Post.objects.create(text=f'Кэш {i}', author=PostsPagesViewsTests.user,) for i in range(3)]
        reverse_name = reverse('posts:index')
        with self.subTest(reverse_name=reverse_name, cache_cleared=False):
            page_before_change = self.client.get(reverse_name).content
            Post.objects.create(
                text='Нет на кэшированной странице',
                author=PostsPagesViewsTests.user,
            )
            page_after_change = self.client.get(reverse_name).content
            self.assertEqual(page_before_change, page_after_change)
        cache.clear()
        page_after_change_cache_cleared = self.client.get(reverse_name).content
        with self.subTest(reverse_name=reverse_name, cache_cleared=True):
            self.assertNotEqual(page_before_change, page_after_change_cache_cleared)


class PaginatorViewsTest(MyTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Текст',
            slug='test-slug'
        )
        cls.user = User.objects.create(username='TestUser')
        for i in range(13):
            Post.objects.create(
                text=f'Тестовый текст {i}',
                group=cls.group,
                author=cls.user,
            )
        cls.reverse_names_limits = {
            reverse('posts:index'): [10, 3],
            reverse('posts:group-post', kwargs={'slug': PaginatorViewsTest.group.slug}): [10, 3],
            reverse('posts:profile', kwargs={'username': PaginatorViewsTest.user.username}): [10, 3],
        }

    def setUp(self):
        cache.clear()

    def test_page_contains_ten_records(self):
        for reverse_name, limits in PaginatorViewsTest.reverse_names_limits.items():
            for page_number in (1, 2):
                with self.subTest(reverse_name=reverse_name, page_number=page_number):
                    response = self.client.get(reverse_name + f'?page={page_number}')
                    page = response.context.get('page')
                    self.assertEqual(page.end_index()-page.start_index()+1, limits[page_number-1])


class FollowViewsTest(MyTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_only = User.objects.create(username='user_only')
        cls.author_user = User.objects.create(username='author_user')
        cls.author_only = User.objects.create(username='author_only')
        cls.users = (cls.user_only, cls.author_user, cls.author_only)
        for user in cls.users:
            [Post.objects.create(text=f'Тестовый текст {user}', author=user,) for i in range(3)]
        Follow.objects.create(user=cls.user_only, author=cls.author_user)
        Follow.objects.create(user=cls.user_only, author=cls.author_only)
        Follow.objects.create(user=cls.author_user, author=cls.author_only)
        cls.reverse_name = reverse('posts:follow_index')

    def setUp(self):
        self.authorized_client = Client()
        cache.clear()

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан на него.."""
        for user in FollowViewsTest.users:
            reverse_name = FollowViewsTest.reverse_name
            with self.subTest(reverse_name=reverse_name, usrname=user.username):
                self.authorized_client.force_login(user)
                response = self.authorized_client.post(reverse_name)
                page = response.context.get('page')
                self.assertEqual(
                    page.paginator.count,
                    page.paginator.object_list.filter(
                        author__in=User.objects.filter(following__user=user)
                    ).count()
                )

    def test_profile_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей."""
        follows_count = Follow.objects.count()
        self.authorized_client.force_login(FollowViewsTest.author_only)
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowViewsTest.user_only.username, }
            ),
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=FollowViewsTest.author_only, author=FollowViewsTest.user_only
            ).exists()
        )

    def test_invalid_profile_follow_same_profile_multiple_times(self):
        """Авторизованный пользователь не может подписываться
        на одного и того же другого пользователя несколько раз."""
        self.authorized_client.force_login(FollowViewsTest.user_only)
        self.assertTrue(
            Follow.objects.filter(
                user=FollowViewsTest.user_only, author=FollowViewsTest.author_only
            ).exists()
        )
        follows_count = Follow.objects.count()
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowViewsTest.author_only.username, }
            ),
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_invalid_profile_follow_non_authorized_user(self):
        """Неавторизованный пользователь не может подписываться
        на других пользователей."""
        follows_count = Follow.objects.count()
        self.client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowViewsTest.user_only.username, }
            ),
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_invalid_self_profile_follow(self):
        """Авторизованный пользователь не может подписываться
        сам на себя."""
        follows_count = Follow.objects.count()
        self.authorized_client.force_login(FollowViewsTest.author_only)
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowViewsTest.author_only.username, }
            ),
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_profile_unfollow(self):
        """Авторизованный пользователь может удалять
        других пользователей из подписок."""
        follows_count = Follow.objects.count()
        self.authorized_client.force_login(FollowViewsTest.user_only)
        self.assertIsInstance(Follow.objects.get(user=FollowViewsTest.user_only, author=FollowViewsTest.author_user), Follow)
        self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': FollowViewsTest.author_user.username, }
            ),
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follows_count-1)
