"""
Burger Bills - Restaurant Menu Management System
Copyright © 2026 Charlie Ah Kuoi. All rights reserved.
Proprietary and confidential. Unauthorized copying or distribution is prohibited.

WSGI config for burgerbills project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'burgerbills.settings')

application = get_wsgi_application()
