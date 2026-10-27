"""
Burger Bills - Restaurant Menu Management System
Copyright © 2026 Charlie Ah Kuoi. All rights reserved.
Proprietary and confidential. Unauthorized copying or distribution is prohibited.

Export and import of menu items, used by the admin panel.

An export is a ZIP holding menu_items.csv plus an images/ folder, so a menu
can be moved between servers with its photos. A plain CSV (no photos) can also
be imported, which is handy for bulk price edits in Excel.
"""

import csv
import io
import os
import zipfile
from decimal import Decimal, InvalidOperation

from django.core.files.base import ContentFile
from django.db import transaction

from .models import Category, MenuItem


CSV_NAME = 'menu_items.csv'
IMAGE_DIR = 'images/'
MAX_UNZIPPED_BYTES = 300 * 1024 * 1024

COLUMNS = [
    'category', 'category_icon', 'category_order',
    'name', 'description', 'price',
    'has_sizes', 'size_small_price', 'size_medium_price', 'size_large_price',
    'is_vegetarian', 'is_vegan', 'is_spicy', 'is_gluten_free',
    'is_available', 'rating', 'order', 'image',
]
BOOL_FIELDS = ['has_sizes', 'is_vegetarian', 'is_vegan', 'is_spicy', 'is_gluten_free', 'is_available']
DECIMAL_FIELDS = ['price', 'size_small_price', 'size_medium_price', 'size_large_price']


class MenuImportError(Exception):
    def __init__(self, errors):
        super().__init__('; '.join(errors))
        self.errors = errors


def _items():
    return MenuItem.objects.select_related('category').order_by('category__order', 'category__name', 'order', 'name')


def _rows(items):
    for item in items:
        yield {
            'category': item.category.name,
            'category_icon': item.category.icon,
            'category_order': item.category.order,
            'name': item.name,
            'description': item.description,
            'price': item.price,
            'has_sizes': item.has_sizes,
            'size_small_price': item.size_small_price,
            'size_medium_price': item.size_medium_price,
            'size_large_price': item.size_large_price,
            'is_vegetarian': item.is_vegetarian,
            'is_vegan': item.is_vegan,
            'is_spicy': item.is_spicy,
            'is_gluten_free': item.is_gluten_free,
            'is_available': item.is_available,
            'rating': item.rating,
            'order': item.order,
            'image': os.path.basename(item.image.name) if item.image else '',
        }


def export_csv():
    """Return the menu as CSV bytes (with a BOM so Excel reads emoji correctly)."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(_rows(_items()))
    return buffer.getvalue().encode('utf-8-sig')


def export_zip():
    """Return a ZIP with the menu CSV and every item photo that can be found."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(CSV_NAME, export_csv())
        written = set()
        for item in _items():
            if not item.image:
                continue
            name = os.path.basename(item.image.name)
            if name in written:
                continue
            try:
                with item.image.open('rb') as image_file:
                    archive.writestr(IMAGE_DIR + name, image_file.read())
            except (FileNotFoundError, OSError):
                continue
            written.add(name)
    return buffer.getvalue()


def _parse_bool(value, field, errors, line):
    text = (value or '').strip().lower()
    if text in ('1', 'true', 'yes', 'y'):
        return True
    if text in ('', '0', 'false', 'no', 'n'):
        return False
    errors.append(f'Row {line}: "{field}" must be yes/no, got "{value}".')
    return False


def _parse_decimal(value, field, errors, line, required=False):
    text = (value or '').strip().lstrip('$')
    if not text:
        if required:
            errors.append(f'Row {line}: "{field}" is required.')
        return Decimal('0')
    try:
        number = Decimal(text)
    except InvalidOperation:
        errors.append(f'Row {line}: "{field}" must be a number, got "{value}".')
        return Decimal('0')
    if number < 0:
        errors.append(f'Row {line}: "{field}" cannot be negative.')
    return number


def _parse_number(value, field, errors, line, cast, default):
    text = (value or '').strip()
    if not text:
        return default
    try:
        return cast(text)
    except ValueError:
        errors.append(f'Row {line}: "{field}" must be a number, got "{value}".')
        return default


def _read_upload(upload):
    """Return (csv_text, images) from an uploaded .csv or .zip file."""
    data = upload.read()
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if sum(info.file_size for info in archive.infolist()) > MAX_UNZIPPED_BYTES:
                raise MenuImportError(['The ZIP file is too large to import.'])
            csv_names = [n for n in archive.namelist() if n.rsplit('/', 1)[-1] == CSV_NAME]
            if not csv_names:
                raise MenuImportError([f'The ZIP file does not contain {CSV_NAME}.'])
            csv_bytes = archive.read(csv_names[0])
            prefix = csv_names[0][:-len(CSV_NAME)] + IMAGE_DIR
            images = {
                os.path.basename(n): archive.read(n)
                for n in archive.namelist()
                if n.startswith(prefix) and not n.endswith('/')
            }
    else:
        csv_bytes, images = data, {}
    try:
        return csv_bytes.decode('utf-8-sig'), images
    except UnicodeDecodeError:
        raise MenuImportError(['The CSV must be saved as UTF-8 ("CSV UTF-8" in Excel).'])


def _apply_image(item, name, images):
    if not name or name not in images:
        return
    if item.image and os.path.basename(item.image.name) == name:
        return
    data = images[name]
    storage = MenuItem._meta.get_field('image').storage
    existing = 'menu_items/' + name
    if storage.exists(existing) and storage.size(existing) == len(data):
        item.image.name = existing
    else:
        item.image.save(name, ContentFile(data), save=False)


def import_menu(upload):
    """
    Create or update menu items from an uploaded export.

    Items are matched by category + name: matches are updated, anything new
    is added, and items missing from the file are left alone. Missing
    categories are created. Nothing is saved if any row is invalid.

    Returns a dict with counts of created and updated items and categories.
    """
    text, images = _read_upload(upload)
    reader = csv.DictReader(io.StringIO(text))
    missing = {'category', 'name', 'price'} - set(reader.fieldnames or [])
    if missing:
        raise MenuImportError([f'Missing column(s): {", ".join(sorted(missing))}.'])

    errors, parsed, seen = [], [], set()
    for line, row in enumerate(reader, start=2):
        category = (row.get('category') or '').strip()
        name = (row.get('name') or '').strip()
        if not category and not name:
            continue
        if not category or not name:
            errors.append(f'Row {line}: "category" and "name" are both required.')
            continue
        key = (category.lower(), name.lower())
        if key in seen:
            errors.append(f'Row {line}: "{name}" appears twice in "{category}".')
            continue
        seen.add(key)

        values = {
            'description': (row.get('description') or '').strip(),
            'rating': _parse_number(row.get('rating'), 'rating', errors, line, float, 0.0),
            'order': _parse_number(row.get('order'), 'order', errors, line, int, 0),
        }
        for field in DECIMAL_FIELDS:
            values[field] = _parse_decimal(row.get(field), field, errors, line, required=field == 'price')
        for field in BOOL_FIELDS:
            if field == 'is_available' and not (row.get(field) or '').strip():
                values[field] = True
            else:
                values[field] = _parse_bool(row.get(field), field, errors, line)
        parsed.append({
            'category': category,
            'category_icon': (row.get('category_icon') or '').strip(),
            'category_order': _parse_number(row.get('category_order'), 'category_order', errors, line, int, None),
            'name': name,
            'image': (row.get('image') or '').strip(),
            'values': values,
        })

    if errors:
        raise MenuImportError(errors)
    if not parsed:
        raise MenuImportError(['The file has no menu items in it.'])

    counts = {'created': 0, 'updated': 0, 'categories_created': 0}
    with transaction.atomic():
        categories = {}
        for row in parsed:
            key = row['category'].lower()
            if key not in categories:
                category = Category.objects.filter(name__iexact=row['category']).first()
                if category is None:
                    category = Category(name=row['category'])
                    counts['categories_created'] += 1
                if row['category_icon']:
                    category.icon = row['category_icon']
                if row['category_order'] is not None:
                    category.order = row['category_order']
                category.save()
                categories[key] = category
            category = categories[key]

            item = MenuItem.objects.filter(category=category, name__iexact=row['name']).first()
            if item is None:
                item = MenuItem(category=category, name=row['name'])
                counts['created'] += 1
            else:
                counts['updated'] += 1
            for field, value in row['values'].items():
                setattr(item, field, value)
            _apply_image(item, row['image'], images)
            item.save()
    return counts
