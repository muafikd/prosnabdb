"""
Полная очистка БД: удаление схемы public (все таблицы и данные) и повторное применение миграций.
Использовать после восстановления не того дампа или для «чистого листа».

Запуск:
  python manage.py reset_db
  python manage.py reset_db --no-input   # без подтверждения
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = (
        'Полностью очистить БД: DROP SCHEMA public CASCADE, создать схему заново, '
        'применить все миграции с нуля. Все данные будут удалены.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Не спрашивать подтверждение.',
        )

    def handle(self, *args, **options):
        if not options['no_input']:
            self.stdout.write(self.style.WARNING(
                'ВНИМАНИЕ: будут удалены ВСЕ таблицы и данные в базе. '
                'После этого будут заново применены миграции.'
            ))
            confirm = input('Продолжить? (yes/no): ')
            if confirm.lower() not in ('yes', 'y'):
                self.stdout.write(self.style.NOTICE('Отменено.'))
                return

        db_name = connection.settings_dict.get('NAME', '')
        self.stdout.write(f'Очистка БД: {db_name}')

        with connection.cursor() as cursor:
            # Удаляем схему public и всё в ней (таблицы, данные, типы и т.д.)
            cursor.execute('DROP SCHEMA IF EXISTS public CASCADE;')
            cursor.execute('CREATE SCHEMA public;')
            cursor.execute('GRANT ALL ON SCHEMA public TO postgres;')
            cursor.execute('GRANT ALL ON SCHEMA public TO public;')
            # Восстанавливаем комментарий для совместимости
            cursor.execute(
                "COMMENT ON SCHEMA public IS 'standard public schema';"
            )

        connection.close()
        self.stdout.write(self.style.SUCCESS('Схема очищена. Применяю миграции...'))

        call_command('migrate', '--run-syncdb', verbosity=2)
        self.stdout.write(self.style.SUCCESS('Готово. База пустая, миграции применены.'))
