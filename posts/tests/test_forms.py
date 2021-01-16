import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()


class NewPostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Текст',
            slug='test-slug'
        )
        cls.user = User.objects.create(username='TestUser')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(NewPostFormTests.user)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'group': NewPostFormTests.group.id,
            'text': 'Новый тестовый текст',
            'image': self.uploaded,
        }
        another_user = User.objects.create(username='AnotherTestUser')
        self.authorized_client.force_login(another_user)
        self.authorized_client.post(reverse('posts:new_post'), data=form_data, follow=True)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(author=another_user).exists())
        new_post = Post.objects.filter(author=another_user).first()
        self.assertEqual(new_post.group.pk, form_data['group'])
        self.assertEqual(new_post.text, form_data['text'])

    def test_edit_post(self):
        """Валидная форма изменяет соответствующую запись
        в базе данных, не создавая новую."""
        posts_count = Post.objects.count()
        form_data = {
            'group': NewPostFormTests.group.id,
            'text': 'Тестовый текст111',
            'image': self.uploaded,
        }
        self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'username': NewPostFormTests.post.author.username,
                    'post_id': NewPostFormTests.post.pk
                }
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        NewPostFormTests.post.refresh_from_db()
        self.assertEqual(NewPostFormTests.post.text, form_data['text'])
        self.assertEqual(NewPostFormTests.post.author, NewPostFormTests.user)
        self.assertEqual(NewPostFormTests.post.group.pk, form_data['group'])

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Новый тестовый комментарий',
        }
        another_user = User.objects.create(username='AnotherTestUser')
        self.authorized_client.force_login(another_user)
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'username': NewPostFormTests.post.author.username,
                    'post_id': NewPostFormTests.post.pk
                }
            ),
            data=form_data,
            follow=True
        )

        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(author=another_user).exists())
        new_comment = Comment.objects.filter(author=another_user).first()
        self.assertEqual(new_comment.text, form_data['text'])


