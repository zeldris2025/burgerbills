import io
import uuid

from django.conf import settings
from django.core.files import File
from django.db import migrations, models

import qrcode


def regenerate_table_qr_codes(apps, schema_editor):
    Table = apps.get_model('menu', 'Table')
    base_url = settings.QR_CODE_BASE_URL.rstrip('/')

    for table in Table.objects.all():
        url = f"{base_url}/table/{table.number}/menu/?access={table.qr_access_token}"
        image = qrcode.make(url)
        buffer = io.BytesIO()
        image.save(buffer, 'PNG')
        buffer.seek(0)
        table.qr_code.save(
            f'qr_code_table_{table.number}.png',
            File(buffer),
            save=False,
        )
        table.save(update_fields=['qr_code'])


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0006_menuitem_is_gluten_free_menuitem_is_vegan_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='table',
            name='qr_access_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.RunPython(regenerate_table_qr_codes, migrations.RunPython.noop),
    ]