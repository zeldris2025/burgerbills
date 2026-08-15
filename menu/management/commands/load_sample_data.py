"""
Django management command to load sample menu data
Run: python manage.py load_sample_data
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from menu.models import Category, MenuItem, Table
import json
import random
from PIL import Image
import io

class Command(BaseCommand):
    help = 'Load sample menu data into the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to load sample data...'))

        # Clear existing data (optional)
        if input('Clear existing data? (y/n): ').lower() == 'y':
            Category.objects.all().delete()
            MenuItem.objects.all().delete()
            Table.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing data'))

        # Sample categories
        categories_data = [
            {
                'name': 'Burgers',
                'description': 'Our signature burgers made with premium beef and fresh ingredients',
                'icon': '🍔',
                'order': 1
            },
            {
                'name': 'Sandwiches',
                'description': 'Delicious sandwiches with a variety of proteins and toppings',
                'icon': '🥪',
                'order': 2
            },
            {
                'name': 'Appetizers',
                'description': 'Start your meal with our crispy and flavorful appetizers',
                'icon': '🍟',
                'order': 3
            },
            {
                'name': 'Salads',
                'description': 'Fresh and healthy salads with house-made dressings',
                'icon': '🥗',
                'order': 4
            },
            {
                'name': 'Pizza',
                'description': 'Wood-fired pizzas with artisan toppings',
                'icon': '🍕',
                'order': 5
            },
            {
                'name': 'Pasta',
                'description': 'Authentic Italian pasta dishes with premium sauces',
                'icon': '🍝',
                'order': 6
            },
            {
                'name': 'Desserts',
                'description': 'Sweet treats and delicious desserts to end your meal',
                'icon': '🍰',
                'order': 7
            },
            {
                'name': 'Drinks',
                'description': 'Refreshing beverages including sodas, juices, and smoothies',
                'icon': '🥤',
                'order': 8
            },
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'order': cat_data['order'],
                }
            )
            categories[cat_data['name']] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {cat.name}'))

        # Sample menu items
        menu_items_data = [
            # Burgers
            {
                'category': 'Burgers',
                'name': 'Classic Cheeseburger',
                'description': 'Juicy beef patty with cheddar cheese, lettuce, tomato, and special sauce',
                'price': 9.99,
                'is_vegetarian': False,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 1,
            },
            {
                'category': 'Burgers',
                'name': 'Bacon Mushroom Burger',
                'description': 'Premium beef burger topped with crispy bacon and sautéed mushrooms',
                'price': 11.99,
                'is_vegetarian': False,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 2,
            },
            {
                'category': 'Burgers',
                'name': 'Spicy Jalapeño Burger',
                'description': 'Beef patty with pepper jack cheese, jalapeños, and chipotle mayo',
                'price': 10.99,
                'is_vegetarian': False,
                'is_vegan': False,
                'is_spicy': True,
                'is_gluten_free': False,
                'order': 3,
            },
            {
                'category': 'Burgers',
                'name': 'Veggie Burger',
                'description': 'Plant-based patty with avocado, tomato, and herb mayo',
                'price': 9.99,
                'is_vegetarian': True,
                'is_vegan': True,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 4,
            },

            # Sandwiches
            {
                'category': 'Sandwiches',
                'name': 'Crispy Chicken Sandwich',
                'description': 'Golden fried chicken breast with coleslaw and creamy sauce',
                'price': 8.99,
                'is_vegetarian': False,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 1,
            },
            {
                'category': 'Sandwiches',
                'name': 'Grilled Fish Sandwich',
                'description': 'Tender grilled fish with tartar sauce and fresh lettuce',
                'price': 9.49,
                'is_vegetarian': False,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 2,
            },
            {
                'category': 'Sandwiches',
                'name': 'Caprese Sandwich',
                'description': 'Fresh mozzarella, tomato, basil, and balsamic vinegar on ciabatta',
                'price': 8.49,
                'is_vegetarian': True,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 3,
            },

            # Appetizers
            {
                'category': 'Appetizers',
                'name': 'French Fries',
                'description': 'Crispy golden fries with sea salt and our signature sauce',
                'price': 4.99,
                'is_vegetarian': True,
                'is_vegan': True,
                'is_spicy': False,
                'is_gluten_free': True,
                'order': 1,
            },
            {
                'category': 'Appetizers',
                'name': 'Loaded Nachos',
                'description': 'Crispy tortilla chips with cheese, jalapeños, and sour cream',
                'price': 7.99,
                'is_vegetarian': True,
                'is_vegan': False,
                'is_spicy': True,
                'is_gluten_free': False,
                'order': 2,
            },
            {
                'category': 'Appetizers',
                'name': 'Mozzarella Sticks',
                'description': 'Golden fried mozzarella cheese served with marinara sauce',
                'price': 6.99,
                'is_vegetarian': True,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 3,
            },
            {
                'category': 'Appetizers',
                'name': 'Buffalo Wings',
                'description': 'Spicy wings tossed in buffalo sauce, served with ranch dip',
                'price': 8.99,
                'is_vegetarian': False,
                'is_vegan': False,
                'is_spicy': True,
                'is_gluten_free': True,
                'order': 4,
            },

            # Salads
            {
                'category': 'Salads',
                'name': 'Caesar Salad',
                'description': 'Crisp romaine lettuce with parmesan cheese and house-made caesar dressing',
                'price': 8.99,
                'is_vegetarian': True,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': True,
                'order': 1,
            },
            {
                'category': 'Salads',
                'name': 'Garden Vegetable Salad',
                'description': 'Mixed greens with seasonal vegetables and balsamic vinaigrette',
                'price': 7.99,
                'is_vegetarian': True,
                'is_vegan': True,
                'is_spicy': False,
                'is_gluten_free': True,
                'order': 2,
            },
            {
                'category': 'Salads',
                'name': 'Grilled Chicken Salad',
                'description': 'Mixed greens with grilled chicken, bacon, and house dressing',
                'price': 10.99,
                'is_vegetarian': False,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': True,
                'order': 3,
            },

            # Pizza
            {
                'category': 'Pizza',
                'name': 'Margherita Pizza',
                'description': 'Classic pizza with fresh mozzarella, tomato, basil, and olive oil',
                'price': 12.99,
                'is_vegetarian': True,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 1,
            },
            {
                'category': 'Pizza',
                'name': 'Pepperoni Pizza',
                'description': 'Classic pepperoni pizza with melted mozzarella on thin crust',
                'price': 13.99,
                'is_vegetarian': False,
                'is_vegan': False,
                'is_spicy': True,
                'is_gluten_free': False,
                'order': 2,
            },
            {
                'category': 'Pizza',
                'name': 'Vegetarian Pizza',
                'description': 'Pizza loaded with fresh vegetables and mozzarella cheese',
                'price': 12.49,
                'is_vegetarian': True,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 3,
            },

            # Pasta
            {
                'category': 'Pasta',
                'name': 'Spaghetti Marinara',
                'description': 'Classic spaghetti tossed in our homemade marinara sauce',
                'price': 10.99,
                'is_vegetarian': True,
                'is_vegan': True,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 1,
            },
            {
                'category': 'Pasta',
                'name': 'Fettuccine Alfredo',
                'description': 'Creamy parmesan sauce over fettuccine with garlic and butter',
                'price': 11.99,
                'is_vegetarian': True,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 2,
            },
            {
                'category': 'Pasta',
                'name': 'Pasta Carbonara',
                'description': 'Authentic carbonara with bacon, eggs, and pecorino cheese',
                'price': 12.99,
                'is_vegetarian': False,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 3,
            },

            # Desserts
            {
                'category': 'Desserts',
                'name': 'Chocolate Cake',
                'description': 'Rich and moist chocolate cake with chocolate frosting',
                'price': 5.99,
                'is_vegetarian': True,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 1,
            },
            {
                'category': 'Desserts',
                'name': 'Cheesecake',
                'description': 'Creamy New York style cheesecake with berry topping',
                'price': 6.99,
                'is_vegetarian': True,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 2,
            },
            {
                'category': 'Desserts',
                'name': 'Vegan Brownies',
                'description': 'Fudgy brownies made with plant-based ingredients',
                'price': 4.99,
                'is_vegetarian': True,
                'is_vegan': True,
                'is_spicy': False,
                'is_gluten_free': False,
                'order': 3,
            },

            # Drinks
            {
                'category': 'Drinks',
                'name': 'Soft Drinks',
                'description': 'Selection of cola, lemonade, and fruit sodas (12 oz)',
                'price': 2.49,
                'is_vegetarian': True,
                'is_vegan': True,
                'is_spicy': False,
                'is_gluten_free': True,
                'order': 1,
            },
            {
                'category': 'Drinks',
                'name': 'Fresh Orange Juice',
                'description': 'Freshly squeezed orange juice (12 oz)',
                'price': 3.49,
                'is_vegetarian': True,
                'is_vegan': True,
                'is_spicy': False,
                'is_gluten_free': True,
                'order': 2,
            },
            {
                'category': 'Drinks',
                'name': 'Smoothie',
                'description': 'Blended fruit smoothie with yogurt (16 oz)',
                'price': 4.99,
                'is_vegetarian': True,
                'is_vegan': False,
                'is_spicy': False,
                'is_gluten_free': True,
                'order': 3,
            },
        ]

        # Create menu items
        for item_data in menu_items_data:
            category = categories[item_data.pop('category')]
            
            menu_item, created = MenuItem.objects.get_or_create(
                name=item_data['name'],
                category=category,
                defaults={**item_data}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created menu item: {menu_item.name}'))

        # Create sample tables
        for table_num in range(1, 11):
            table, created = Table.objects.get_or_create(
                number=table_num,
                defaults={
                    'capacity': random.choice([2, 4, 6, 8]),
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created table: {table.number}'))

        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully!'))
        self.stdout.write(self.style.WARNING('Tables created: 1-10'))
        self.stdout.write(self.style.WARNING('Categories created: Burgers, Sandwiches, Appetizers, Salads, Pizza, Pasta, Desserts, Drinks'))
        self.stdout.write(self.style.WARNING(f'Menu items created: {len(menu_items_data)}'))
