from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, override_settings
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

    def test_profile_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок."""
        follows_count = Follow.objects.count()
        another_user = User.objects.create(username='AnotherTestUser')
        self.authorized_client.force_login(another_user)
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostsPagesViewsTests.user.username,}
            ),
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        self.assertTrue(Follow.objects.filter(user=another_user).exists())
        new_follow = Follow.objects.filter(user=another_user).first()
        self.assertEqual(new_follow.author, PostsPagesViewsTests.user)
        self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostsPagesViewsTests.user.username, }
            ),
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follows_count)


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

    def test_page_contains_ten_records(self):
        for reverse_name, limits in PaginatorViewsTest.reverse_names_limits.items():
            for page_number in (1, 2):
                with self.subTest(reverse_name=reverse_name, page_number=page_number):
                    response = self.client.get(reverse_name + f'?page={page_number}')
                    page = response.context.get('page')
                    self.assertEqual(page.end_index()-page.start_index()+1, limits[page_number-1])


    def test_index_page_caches_posts_items(self):
        cache.clear()
        self.maxDiff = None
        reverse_name = reverse('posts:index')
        with self.subTest(reverse_name=reverse_name, cache_cleared=False):
            page2_1 = self.client.get(reverse_name).content
            Post.objects.create(
                text=f'Тестируем кэширование 2',
                author=PaginatorViewsTest.user,
            )
            page_2_2 = self.client.get(reverse_name).content
            self.assertHTMLEqual(str(page2_1), str(page_2_2))
        cache.clear()
        page_2_2 = self.client.get(reverse_name).content
        with self.subTest(reverse_name=reverse_name, cache_cleared=True):
            self.assertHTMLNotEqual(str(page2_1), str(page_2_2))


class FollowViewsTest(MyTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = []
        for i in range(3):
            cls.user.append(User.objects.create(username=f'TestUser_{i}'))
            for j in range(3):
                Post.objects.create(
                    text=f'Тестовый текст {j}',
                    author=cls.user[i],
                )
        Follow.objects.create(user=cls.user[0], author=cls.user[1])
        Follow.objects.create(user=cls.user[1], author=cls.user[2])
        cls.reverse_names_limits = {reverse('posts:follow_index'): [3, 3, 0]}

    def setUp(self):
        self.authorized_client = Client()

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан на него.."""
        for reverse_name, limits in FollowViewsTest.reverse_names_limits.items():
            for i in range(3):
                with self.subTest(reverse_name=reverse_name, usrname=FollowViewsTest.user[i]):
                    self.authorized_client.force_login(FollowViewsTest.user[i])
                    response = self.authorized_client.post(reverse_name)
                    page = response.context.get('page')
                    self.assertEqual(page.paginator.count, limits[i])
                    self.assertEqual(
                        page.paginator.object_list.filter(
                            author=FollowViewsTest.user[0 if i == 2 else i+1]).count(), limits[i]
                    )
