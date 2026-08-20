from django.core.management.base import BaseCommand

from menu.models import Table


class Command(BaseCommand):
    help = 'Regenerate every table QR code using the configured QR_CODE_BASE_URL'

    def handle(self, *args, **options):
        regenerated = 0
        for table in Table.objects.iterator():
            table.qr_code = None
            table.save(update_fields=['qr_code'])
            regenerated += 1

        self.stdout.write(self.style.SUCCESS(f'Regenerated {regenerated} table QR code(s)'))