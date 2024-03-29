# Generated by Django 2.2.6 on 2021-01-11 09:24

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('posts', '0009_post_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, help_text='Выберите изображение для загрузки с компьютера', null=True, upload_to='posts/', verbose_name='Изображение'),
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(help_text='Напишите здесь текст комментария', verbose_name='Текст')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='Дата комментария устанавливается автоматически', verbose_name='Дата комментария')),
                ('author', models.ForeignKey(help_text='Автор комментария устанавливается автоматически', on_delete=django.db.models.deletion.CASCADE, related_name='comments', to=settings.AUTH_USER_MODEL, verbose_name='Автор комментария')),
                ('post', models.ForeignKey(help_text='Выберите из списка публикацию для комментирования', on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='posts.Post', verbose_name='Публикация')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
    ]
