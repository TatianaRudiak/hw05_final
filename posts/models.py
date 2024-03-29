from django.contrib.auth import get_user_model
from django.core.validators import ValidationError
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint
from django.urls import reverse
from django.utils.translation import gettext_lazy

from .constants import LABELS

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name=LABELS['Group']['title']['verbose_name'],
        help_text=LABELS['Group']['title']['help_text'],
        max_length=200,
    )
    slug = models.SlugField(
        verbose_name=LABELS['Group']['slug']['verbose_name'],
        help_text=LABELS['Group']['slug']['help_text'],
        max_length=30,
        unique=True,
    )
    description = models.TextField(
        verbose_name=LABELS['Group']['description']['verbose_name'],
        help_text=LABELS['Group']['description']['help_text'],
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('posts:group-post', kwargs={'slug': self.slug})


class Post(models.Model):
    text = models.TextField(
        verbose_name=LABELS['Post']['text']['verbose_name'],
        help_text=LABELS['Post']['text']['help_text'],
    )
    pub_date = models.DateTimeField(
        verbose_name=LABELS['Post']['pub_date']['verbose_name'],
        help_text=LABELS['Post']['pub_date']['help_text'],
        auto_now_add=True,
        db_index=True
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='posts',
        verbose_name=LABELS['Post']['author']['verbose_name'],
        help_text=LABELS['Post']['author']['help_text'],
    )
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name=LABELS['Post']['group']['verbose_name'],
        help_text=LABELS['Post']['group']['help_text']
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        null=True,
        verbose_name=LABELS['Post']['image']['verbose_name'],
        help_text=LABELS['Post']['image']['help_text']
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]

    def get_absolute_url(self):
        return reverse(
            'posts:post',
            kwargs={
                'username': self.author.username,
                'post_id': self.pk
            }
        )


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'Комментарий @{self.author}'


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'author'], name='unique_follow'),
            CheckConstraint(check=~Q(user=F('author')), name='user_not_author'),
        ]

    def clean(self):
        if self.user == self.author:
            raise ValidationError({'user_not_author': gettext_lazy('Пользователь не может подписаться сам на себя.')})
