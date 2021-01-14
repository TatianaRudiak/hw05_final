from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class StaticPagesURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.templates_reverse_names = {
            'about/about.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticPagesURLTests.user)

    def test_url_exists_at_desired_location_all_users(self):
        """Проверка доступности адреса для авторизованного и НЕавторизованного пользователя."""
        for reverse_name in StaticPagesURLTests.templates_reverse_names.values():
            for client in (self.client, self.authorized_client):
                with self.subTest(reverse_name=reverse_name, client=client.cookies):
                    response = client.get(reverse_name)
                    self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in StaticPagesURLTests.templates_reverse_names.items():
            with self.subTest(template=template):
                response = self.client.get(reverse_name)
                self.assertTemplateUsed(response, template)
