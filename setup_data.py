"""
Burger Bills - Restaurant Menu Management System
Copyright © 2026 Charlie Ah Kuoi. All rights reserved.
Proprietary and confidential. Unauthorized copying or distribution is prohibited.
"""

from menu.models import Category, MenuItem, Table

# Create categories
burger_cat = Category.objects.create(name="Burgers", icon="🍔", order=1)
drink_cat = Category.objects.create(name="Drinks", icon="🥤", order=2)
sides_cat = Category.objects.create(name="Sides", icon="🍟", order=3)
dessert_cat = Category.objects.create(name="Desserts", icon="🍰", order=4)

# Create burger items
MenuItem.objects.create(
    category=burger_cat,
    name="Classic Burger",
    description="Juicy beef patty with lettuce, tomato, and special sauce",
    price=12.99,
    is_available=True,
    rating=4.5
)

MenuItem.objects.create(
    category=burger_cat,
    name="Cheese Burger",
    description="Double cheese, beef patty, pickles, and onions",
    price=14.99,
    is_available=True,
    rating=4.7
)

MenuItem.objects.create(
    category=burger_cat,
    name="Spicy Burger",
    description="Hot sauce, jalapeños, and crispy bacon",
    price=15.99,
    is_available=True,
    is_spicy=True,
    rating=4.4
)

MenuItem.objects.create(
    category=burger_cat,
    name="Veggie Burger",
    description="Plant-based patty with fresh vegetables",
    price=13.99,
    is_available=True,
    is_vegetarian=True,
    rating=4.2
)

# Create drink items
MenuItem.objects.create(
    category=drink_cat,
    name="Coca Cola",
    description="Classic cold cola drink",
    price=3.99,
    is_available=True,
    rating=4.5
)

MenuItem.objects.create(
    category=drink_cat,
    name="Fresh Orange Juice",
    description="Freshly squeezed orange juice",
    price=5.99,
    is_available=True,
    is_vegetarian=True,
    rating=4.6
)

MenuItem.objects.create(
    category=drink_cat,
    name="Iced Coffee",
    description="Cold coffee with ice",
    price=4.99,
    is_available=True,
    rating=4.4
)

# Create sides items
MenuItem.objects.create(
    category=sides_cat,
    name="French Fries",
    description="Crispy golden fries with salt",
    price=4.99,
    is_available=True,
    is_vegetarian=True,
    rating=4.6
)

MenuItem.objects.create(
    category=sides_cat,
    name="Onion Rings",
    description="Crispy onion rings with dipping sauce",
    price=5.99,
    is_available=True,
    is_vegetarian=True,
    rating=4.5
)

MenuItem.objects.create(
    category=sides_cat,
    name="Chicken Nuggets",
    description="6 piece crispy chicken nuggets",
    price=6.99,
    is_available=True,
    rating=4.7
)

# Create dessert items
MenuItem.objects.create(
    category=dessert_cat,
    name="Chocolate Cake",
    description="Rich and delicious chocolate cake",
    price=6.99,
    is_available=True,
    is_vegetarian=True,
    rating=4.8
)

MenuItem.objects.create(
    category=dessert_cat,
    name="Ice Cream Sundae",
    description="Vanilla ice cream with toppings",
    price=5.99,
    is_available=True,
    is_vegetarian=True,
    rating=4.7
)

# Create tables
for i in range(1, 11):
    Table.objects.create(number=i, capacity=4 if i <= 5 else 6)

print("✅ Sample data created successfully!")
