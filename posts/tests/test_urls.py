from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostPagesURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug='test-slug'
        )
        cls.user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(
            id=1,
            text='Тестовый текст',
            group=cls.group,
            author=cls.user
        )
        cls.url_names_kwargs = {
            reverse('posts:index'): {'status_codes': [200, 200], 'template': 'posts/index.html'},
            reverse('posts:groups'): {'status_codes': [200, 200], 'template': 'posts/groups.html'},
            reverse('posts:new_post'): {
                'status_codes': [200, 302],
                'template': 'posts/new_post.html',
            },
            reverse('posts:group-post', kwargs={'slug': cls.group.slug}): {
                'status_codes': [200, 200],
                'template': 'posts/group.html'
            },
            reverse('posts:profile', kwargs={'username': cls.user.username}): {
                'status_codes': [200, 200],
                'template': 'posts/profile.html'
            },
            reverse('posts:post', kwargs={'username': cls.post.author.username, 'post_id': cls.post.pk}): {
                'status_codes': [200, 200],
                'template': 'posts/post.html'
            },
            reverse('posts:post_edit', kwargs={'username': cls.post.author.username, 'post_id': cls.post.pk}): {
                'status_codes': [200, 302],
                'template': 'posts/new_post.html',
            },
            reverse('posts:add_comment', kwargs={'username': cls.post.author.username, 'post_id': cls.post.pk}): {
                'status_codes': [302, 302],
                'template_redirect': reverse(
                    'posts:post',
                    kwargs={'username': cls.post.author.username, 'post_id': cls.post.pk})+'#add_comment'
            },
            reverse('posts:follow_index'): {
                'status_codes': [200, 302],
                'template': 'posts/follow.html',
            },
            reverse('posts:followees'): {
                'status_codes': [200, 302],
                'template': 'posts/followees.html',
            },
            reverse('posts:followers'): {
                'status_codes': [200, 302],
                'template': 'posts/followers.html',
            },
            reverse('posts:profile_follow', kwargs={'username': cls.user.username}): {
                'status_codes': [302, 302],
            },
            reverse('posts:profile_unfollow', kwargs={'username': cls.user.username}): {
                'status_codes': [302, 302],
            },
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesURLTests.user)
        cache.clear()

    def test_url_status_code_404(self):
        """Проверка возвращает ли сервер код 404, если страница не найдена."""
        clients = [self.authorized_client, self.client]
        for i in range(len(clients)):
            with self.subTest(client=clients[i], url_name='test_url_status_code_404'):
                response = clients[i].get('test_url_status_code_404')
                self.assertEqual(response.status_code, 404)

    def test_url_exists_at_desired_location(self):
        """Проверка доступности адреса для авторизованного и НЕавторизованного пользователя."""
        for url_name, kwargs in PostPagesURLTests.url_names_kwargs.items():
            clients = [self.authorized_client, self.client]
            for i, client in enumerate(clients):
                with self.subTest(client=client, url_name=url_name):
                    response = client.get(url_name)
                    self.assertEqual(response.status_code, kwargs['status_codes'][i])

    def test_url_redirect_nonauthor_on_post_page(self):
        """Страница по адресу /<username>/<post_id>/edit/ перенаправит
        авторизованного пользователя — не автора поста
        на страницу /<username>/<post_id>/ просмотра этого поста.
        """
        self.another_user = User.objects.create_user(
            username='AnotherTestUser'
        )
        self.authorized_client.force_login(self.another_user)
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={
                'username': PostPagesURLTests.post.author.username,
                'post_id': PostPagesURLTests.post.pk
            }),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post', kwargs={
                'username': PostPagesURLTests.post.author.username,
                'post_id': PostPagesURLTests.post.pk
            })
        )

    def test_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу перенаправит анонимного
        пользователя на страницу логина.
        """
        for url_name, kwargs in PostPagesURLTests.url_names_kwargs.items():
            if 302 in kwargs['status_codes']:
                with self.subTest(url_name=url_name):
                    response = self.client.get(url_name, follow=True)
                    self.assertRedirects(response, reverse('login')+'?next='+url_name)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url_name, kwargs in PostPagesURLTests.url_names_kwargs.items():
            if 'template' in kwargs:
                with self.subTest(url_name=url_name):
                    response = self.authorized_client.get(url_name)
                    self.assertTemplateUsed(response, kwargs['template'])

    def test_urls_redirect_correct_template(self):
        """Страница по адресу перенаправит авторизованного
        пользователя на соответствующую страницу.
        """
        for url_name, kwargs in PostPagesURLTests.url_names_kwargs.items():
            if 'template_redirect' in kwargs:
                with self.subTest(url_name=url_name, template_redirect=kwargs['template_redirect']):
                    response = self.authorized_client.get(url_name, follow=True)
                    self.assertRedirects(response, kwargs['template_redirect'])
