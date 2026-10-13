"""
Burger Bills - Restaurant Menu Management System
Copyright © 2026 Charlie Ah Kuoi. All rights reserved.
Proprietary and confidential. Unauthorized copying or distribution is prohibited.
"""

from django import forms

from .models import Promotion


MAX_PROMOTION_IMAGE_MB = 10


class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = [
            'title', 'tagline', 'badge', 'description', 'hero_image',
            'price', 'original_price', 'price_note',
            'starts_at', 'ends_at', 'daily_start_time', 'daily_end_time',
            'terms', 'is_published', 'display_order',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'ends_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'daily_start_time': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'daily_end_time': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'hero_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }
        labels = {
            'hero_image': 'Hero photo',
            'original_price': 'Was price',
            'starts_at': 'Starts',
            'ends_at': 'Ends',
            'daily_start_time': 'Daily from',
            'daily_end_time': 'Daily until',
            'is_published': 'Published',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'form-check-input')
            else:
                widget.attrs.setdefault('class', 'form-control')
        for name in ('price', 'original_price'):
            self.fields[name].widget.attrs.update({'min': '0', 'step': '0.01'})

    def clean_hero_image(self):
        image = self.cleaned_data.get('hero_image')
        if image and getattr(image, 'size', 0) > MAX_PROMOTION_IMAGE_MB * 1024 * 1024:
            raise forms.ValidationError(f'Please upload a photo smaller than {MAX_PROMOTION_IMAGE_MB} MB.')
        return image

    def clean(self):
        cleaned = super().clean()
        starts_at, ends_at = cleaned.get('starts_at'), cleaned.get('ends_at')
        if starts_at and ends_at and ends_at <= starts_at:
            self.add_error('ends_at', 'The promotion has to end after it starts.')

        price, original = cleaned.get('price'), cleaned.get('original_price')
        if original is not None and price is None:
            self.add_error('price', 'Add the promotion price to show a "was" price.')
        elif original is not None and original <= price:
            self.add_error('original_price', 'The "was" price should be higher than the promotion price.')

        daily_start, daily_end = cleaned.get('daily_start_time'), cleaned.get('daily_end_time')
        if bool(daily_start) != bool(daily_end):
            self.add_error('daily_end_time' if daily_start else 'daily_start_time', 'Set both daily times, or leave both empty.')
        elif daily_start and daily_end <= daily_start:
            self.add_error('daily_end_time', 'The daily end time has to be after the start time.')
        return cleaned
