"""Management command to generate MCP API token for a user."""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Generate MCP API token for a user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username')
        parser.add_argument('--admin', action='store_true', help='Ensure user is admin')
        parser.add_argument('--name', type=str, default='MCP Token', help='Token name')

    def handle(self, *args, **options):
        username = options['username']
        make_admin = options['admin']
        token_name = options['name']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(f"User '{username}' does not exist")
            return

        if make_admin and not user.is_superuser:
            user.is_superuser = True
            user.is_staff = True
            user.save(update_fields=['is_superuser', 'is_staff'])
            self.stdout.write(self.style.SUCCESS(f"Made {username} a superuser"))

        # Import here to avoid circular imports
        from bookstore.models import APIToken

        # Generate token using the model
        token_obj, token_key = APIToken.generate_token(user=user, name=token_name)

        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        self.stdout.write(self.style.SUCCESS(f"MCP API Token for {username}"))
        self.stdout.write(self.style.SUCCESS(f"{'='*60}\n"))
        self.stdout.write(f"Token ID: {token_obj.id}")
        self.stdout.write(f"Token Name: {token_obj.name}")
        self.stdout.write(f"Created: {token_obj.created_at}")
        self.stdout.write(self.style.SUCCESS(f"\nAPI Token: {token_key}"))
        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        self.stdout.write(self.style.SUCCESS("Usage - 在 MCP 客户端调用时传递以下 header："))
        self.stdout.write(self.style.SUCCESS(f'Authorization: Token {token_key}'))
        self.stdout.write(self.style.SUCCESS(f"或"))
        self.stdout.write(self.style.SUCCESS(f'Authorization: Bearer {token_key}'))
        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        self.stdout.write(self.style.WARNING("\n注意：Token 只显示这一次，请妥善保存！"))