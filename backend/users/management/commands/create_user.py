from decouple import config
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    """
    Create a admin-user for app
    """
    help = "Creates a single application user, typically an owner."

    def add_arguments(self, parser):
        parser.add_argument(
            '--role',
            type=str,
            help='Specify the role of the user (e.g., "owner")',
            default='owner'
        )

    def handle(self, *args, **options):
        username = config('ADMIN_USER')
        email = config('ADMIN_EMAIL')
        password = config('ADMIN_PASS')
        role = options['role']

        if not all([username, email, password]):
            self.stderr.write(self.style.ERROR(
                "Ошибка: Переменные окружения ADMIN_USER, ADMIN_EMAIL, "
                "и ADMIN_PASS должны быть установлены."
            ))
            return

        if role != 'owner':
            self.stderr.write(self.style.WARNING(
                f"Роль '{role}' не поддерживается. Будет создан 'owner'."
            ))
            role = 'owner'

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(
                f"Пользователь '{username}' уже существует. Обновление не требуется."
            ))
            return

        if role == 'owner':
            try:
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(self.style.SUCCESS(
                    f"Суперпользователь '{username}' успешно создан."
                ))
            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    f"Ошибка при создании суперпользователя: {e}"
                ))
        else:
            self.stderr.write(self.style.ERROR(
                "Поддерживается только создание пользователя с --role=owner"
            ))