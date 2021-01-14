LABELS = {
    'Group': {
        'title': {'verbose_name': 'Название группы', 'help_text': 'Введите название группы'},
        'slug': {'verbose_name': 'Slug группы', 'help_text': 'Введите уникальный slug группы'},
        'description': {'verbose_name': 'Описание группы', 'help_text': 'Введите описание группы'}
    },
    'Post': {
        'text': {'verbose_name': 'Текст', 'help_text': 'Напишите здесь текст публикации'},
        'pub_date': {
            'verbose_name': 'Дата публикации',
            'help_text': 'Дата публикации устанавливается автоматически'
        },
        'author': {
            'verbose_name': 'Автор публикации',
            'help_text': 'Автор публикации устанавливается автоматически'
        },
        'group': {
            'verbose_name': 'Группа',
            'help_text': 'Выберите группу из списка, или оставьте поле пустым'
        },
        'image': {
            'verbose_name': 'Изображение',
            'help_text': 'Выберите c локального диска изображение для загрузки'
        },
    },
    'Comment': {
        'text': {'verbose_name': 'Текст', 'help_text': 'Напишите здесь текст комментария'},
        'created': {
            'verbose_name': 'Дата комментария',
            'help_text': 'Дата комментария устанавливается автоматически'
        },
        'author': {
            'verbose_name': 'Автор комментария',
            'help_text': 'Автор комментария устанавливается автоматически'
        },
        'post': {
            'verbose_name': 'Публикация',
            'help_text': 'Выберите из списка публикацию для комментирования'
        },
    },
}
