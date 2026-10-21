import io
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .models import Category, MenuItem, Order, OrderItem, Promotion, Table


_test_media = tempfile.TemporaryDirectory()
_media_override = override_settings(MEDIA_ROOT=_test_media.name)


def setUpModule():
	_media_override.enable()


def tearDownModule():
	_media_override.disable()
	_test_media.cleanup()


class LandingPageTests(TestCase):
	def test_root_renders_public_website(self):
		response = self.client.get(reverse("index"))

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "menu/index.html")
		self.assertContains(response, "Burger Bills")
		self.assertContains(response, "scan your table's QR code")

	def test_root_has_no_staff_admin_or_customer_links(self):
		response = self.client.get(reverse("index"))

		self.assertNotContains(response, 'href="/staff/')
		self.assertNotContains(response, 'href="/admin/')
		self.assertNotContains(response, 'href="/table/')

	def test_root_shows_hot_deals_combos_and_meals_from_menu(self):
		deals = Category.objects.create(name="New & Hot Deals", order=0)
		combos = Category.objects.create(name="Combos", order=1)
		meals = Category.objects.create(name="Meal", order=2)
		burgers = Category.objects.create(name="Burgers", order=3)
		MenuItem.objects.create(category=deals, name="Fiafia Meal", description="Deal", price="17.00")
		MenuItem.objects.create(category=combos, name="Share Box", description="Box", price="140.00")
		MenuItem.objects.create(
			category=meals, name="Fish & Chips", description="Meal", price="15.50",
			has_sizes=True, size_small_price="15.50", size_large_price="17.50",
		)
		MenuItem.objects.create(category=meals, name="Sold Out Meal", description="Meal", price="9.00", is_available=False)
		MenuItem.objects.create(category=burgers, name="Plain Burger", description="Burger", price="8.00")

		response = self.client.get(reverse("index"))

		self.assertContains(response, "Fiafia Meal")
		self.assertContains(response, "Share Box")
		self.assertContains(response, "Fish &amp; Chips")
		self.assertContains(response, "$17.50")
		self.assertNotContains(response, "Sold Out Meal")
		self.assertNotContains(response, "Plain Burger")
		self.assertEqual(
			[section["key"] for section in response.context["menu_sections"]],
			["hot-deals", "combos", "meals"],
		)


class OrderItemTests(TestCase):
	def test_string_representation_handles_deleted_menu_item(self):
		order_item = OrderItem(quantity=2, menu_item=None)

		self.assertEqual(str(order_item), "2x Deleted menu item")


class TableQrCodeTests(TestCase):
	def test_direct_table_url_is_rejected_without_qr_token(self):
		table = Table.objects.create(number=102)

		response = self.client.get(reverse("table_menu", args=[table.number]))

		self.assertEqual(response.status_code, 404)

	def test_qr_token_grants_table_session_access(self):
		table = Table.objects.create(number=103)

		response = self.client.get(
			reverse("table_menu", args=[table.number]),
			{"access": str(table.qr_access_token)},
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(self.client.session["qr_table_number"], table.number)
		self.assertEqual(
			self.client.get(reverse("current_order_items", args=[table.number])).status_code,
			200,
		)

	def test_qr_menu_url_contains_unpredictable_table_token(self):
		table = Table.objects.create(number=104)

		self.assertEqual(
			table.get_qr_menu_url(),
			f"https://burgerbills.ws/table/104/menu/?access={table.qr_access_token}",
		)

	def test_request_recreates_qr_code_when_image_was_deleted(self):
		with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
			table = Table.objects.create(number=100)
			qr_code_name = table.qr_code.name
			table.qr_code.storage.delete(qr_code_name)

			self.assertFalse(table.qr_code.storage.exists(qr_code_name))

			response = self.client.get(reverse("table_qr_code", args=[table.number]))

			self.assertEqual(response.status_code, 200)
			self.assertEqual(response["Content-Type"], "image/png")
			self.assertTrue(table.qr_code.storage.exists(qr_code_name))
			response.close()

	def test_regeneration_reuses_table_qr_filename(self):
		table = Table.objects.create(number=101)
		qr_code_name = table.qr_code.name

		table.qr_code = None
		table.save()

		self.assertEqual(table.qr_code.name, qr_code_name)

	def test_regeneration_command_replaces_existing_qr_code(self):
		table = Table.objects.create(number=105)
		qr_code_name = table.qr_code.name
		table.qr_code.storage.delete(qr_code_name)
		table.qr_code.storage.save(qr_code_name, ContentFile(b"stale QR code"))

		call_command("regenerate_qr_codes", verbosity=0)
		table.refresh_from_db()

		self.assertEqual(table.qr_code.name, qr_code_name)
		with table.qr_code.open("rb") as qr_code_file:
			self.assertEqual(qr_code_file.read(8), b"\x89PNG\r\n\x1a\n")


class OrderAdminTests(TestCase):
	def test_bulk_delete_handles_order_item_with_deleted_menu_item(self):
		admin_user = get_user_model().objects.create_superuser(
			username="admin",
			email="admin@example.com",
			password="password",
		)
		table = Table.objects.create(number=99)
		order = Order.objects.create(order_number="ORD-DELETE-TEST", table=table)
		OrderItem.objects.create(
			order=order,
			menu_item=None,
			quantity=1,
			unit_price="9.99",
		)
		self.client.force_login(admin_user)

		response = self.client.post(
			reverse("admin:menu_order_changelist"),
			{
				"action": "delete_selected",
				"_selected_action": [str(order.pk)],
				"post": "yes",
			},
		)

		self.assertRedirects(response, reverse("admin:menu_order_changelist"))
		self.assertFalse(Order.objects.filter(pk=order.pk).exists())


class StaffOrderReceiptTests(TestCase):
	def setUp(self):
		self.table = Table.objects.create(number=96)
		self.order = Order.objects.create(
			order_number="ORD-STAFF-RECEIPT",
			table=self.table,
			total_amount="12.00",
		)

	def test_staff_can_view_order_receipt(self):
		staff_user = get_user_model().objects.create_user(
			username="staff-receipt",
			password="password",
			is_staff=True,
		)
		self.client.force_login(staff_user)

		response = self.client.get(reverse("staff_order_receipt", args=[self.order.pk]))

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "menu/receipt.html")
		self.assertContains(response, self.order.order_number)
		self.assertContains(response, f'href="{reverse("all_orders")}"')

	def test_non_staff_cannot_view_order_receipt(self):
		customer = get_user_model().objects.create_user(
			username="customer-receipt",
			password="password",
		)
		self.client.force_login(customer)

		response = self.client.get(reverse("staff_order_receipt", args=[self.order.pk]))

		self.assertRedirects(response, reverse("staff_login"))


class LogoutTests(TestCase):
	def test_refresh_only_runs_on_authenticated_staff_panel(self):
		login_response = self.client.get(reverse("staff_login"))

		self.assertNotContains(login_response, "location.reload()")

		staff_user = get_user_model().objects.create_user(
			username="staff-refresh",
			password="password",
			is_staff=True,
		)
		self.client.force_login(staff_user)

		panel_response = self.client.get(reverse("staff_panel"))

		self.assertContains(
			panel_response,
			"setTimeout(() => location.reload(), 5000)",
		)

	def test_staff_logout_clears_session_and_returns_to_staff_login(self):
		staff_user = get_user_model().objects.create_user(
			username="staff-logout",
			password="password",
			is_staff=True,
		)
		self.client.force_login(staff_user)

		panel_response = self.client.get(reverse("staff_panel"))
		self.assertContains(panel_response, f'href="{reverse("staff_logout")}"')
		self.assertNotContains(panel_response, 'href="/admin/logout/"')

		response = self.client.get(reverse("staff_logout"))

		self.assertRedirects(response, reverse("staff_login"))
		self.assertNotIn("_auth_user_id", self.client.session)

	def test_manager_logout_clears_session_and_returns_to_manager_login(self):
		manager = get_user_model().objects.create_superuser(
			username="manager-logout",
			email="manager@example.com",
			password="password",
		)
		self.client.force_login(manager)

		panel_response = self.client.get(reverse("manager_panel"))
		self.assertContains(panel_response, f'href="{reverse("manager_logout")}"')

		response = self.client.get(reverse("manager_logout"))

		self.assertRedirects(response, reverse("manager_login"))
		self.assertNotIn("_auth_user_id", self.client.session)


class MarqueeSettingsTests(TestCase):
	def test_customer_menu_uses_configured_marquee(self):
		from .models import MarqueeSettings

		settings = MarqueeSettings.load()
		settings.customer_message = "Customer special: free fries today"
		settings.save()
		table = Table.objects.create(number=94)

		response = self.client.get(
			reverse("table_menu", args=[table.number]),
			{"access": str(table.qr_access_token)},
		)

		self.assertContains(response, settings.customer_message, count=2)

	def test_staff_panel_uses_configured_marquee(self):
		from .models import MarqueeSettings

		settings = MarqueeSettings.load()
		settings.staff_message = "Staff reminder: check pickup orders"
		settings.save()
		staff_user = get_user_model().objects.create_user(
			username="staff-marquee",
			password="password",
			is_staff=True,
		)
		self.client.force_login(staff_user)

		response = self.client.get(reverse("staff_panel"))

		self.assertContains(response, settings.staff_message)

	def test_marquee_settings_are_available_in_admin(self):
		from django.contrib import admin
		from .models import MarqueeSettings

		self.assertIn(MarqueeSettings, admin.site._registry)


class CancelOrderItemTests(TestCase):
	def test_cancel_item_updates_total_and_deletes_empty_order(self):
		table = Table.objects.create(number=98)
		order = Order.objects.create(
			order_number="ORD-CANCEL-TEST",
			table=table,
			total_amount="25.00",
		)
		first_item = OrderItem.objects.create(
			order=order,
			menu_item=None,
			quantity=1,
			unit_price="10.00",
		)
		second_item = OrderItem.objects.create(
			order=order,
			menu_item=None,
			quantity=1,
			unit_price="15.00",
		)
		self.client.get(
			reverse("table_menu", args=[table.number]),
			{"access": str(table.qr_access_token)},
		)

		response = self.client.post(
			reverse("remove_from_cart", args=[table.number, first_item.pk]),
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["total_amount"], "15.00")
		self.assertFalse(OrderItem.objects.filter(pk=first_item.pk).exists())

		response = self.client.post(
			reverse("remove_from_cart", args=[table.number, second_item.pk]),
		)

		self.assertTrue(response.json()["order_deleted"])
		self.assertFalse(Order.objects.filter(pk=order.pk).exists())


class CheckoutTests(TestCase):
	def test_checkout_confirms_order_and_links_to_status(self):
		table = Table.objects.create(number=97)
		order = Order.objects.create(order_number="ORD-CHECKOUT-TEST", table=table)
		OrderItem.objects.create(
			order=order,
			menu_item=None,
			quantity=1,
			unit_price="12.00",
		)
		self.client.get(
			reverse("table_menu", args=[table.number]),
			{"access": str(table.qr_access_token)},
		)

		response = self.client.get(reverse("checkout", args=[table.number]))

		order.refresh_from_db()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(order.status, "confirmed")
		self.assertContains(response, "Thank you for ordering")
		self.assertContains(
			response,
			reverse("order_status", args=[table.number, order.pk]),
		)


class OrderCompletionAlertTests(TestCase):
	def authorize_table(self, table):
		return self.client.get(
			reverse("table_menu", args=[table.number]),
			{"access": str(table.qr_access_token)},
		)

	def test_status_endpoint_returns_live_order_state(self):
		table = Table.objects.create(number=95)
		order = Order.objects.create(
			order_number="ORD-STATUS-TEST",
			table=table,
			status="ready",
		)
		self.authorize_table(table)

		response = self.client.get(
			reverse("order_status_data", args=[table.number, order.pk]),
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json(), {"status": "ready", "is_called": False})

	def test_completed_order_status_contains_customer_alert(self):
		table = Table.objects.create(number=96)
		order = Order.objects.create(
			order_number="ORD-COMPLETE-TEST",
			table=table,
			status="completed",
		)
		self.authorize_table(table)

		response = self.client.get(
			reverse("order_status", args=[table.number, order.pk]),
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'id="completion-alert"')
		self.assertContains(response, "Order complete!")
		self.assertContains(response, order.order_number)
		self.assertContains(response, "Collect your order now at the counter.")
		self.assertContains(response, "playCompletionChime")
		self.assertContains(response, "window.AudioContext || window.webkitAudioContext")
		self.assertContains(response, "window.setInterval(playCompletionChime, 1000)")
		self.assertContains(response, "window.clearInterval(completionChimeTimer)")
		self.assertContains(response, "let completionAudioContext = null")
		self.assertContains(response, "document.addEventListener('touchstart', unlockAlerts")
		self.assertContains(response, "if (!alertOverlay.hidden)")
		self.assertContains(response, "window.setTimeout(dismissAlert, 750)")

	def test_pending_order_refreshes_progress_and_checks_mobile_alerts(self):
		table = Table.objects.create(number=94)
		order = Order.objects.create(
			order_number="ORD-MOBILE-ALERT-TEST",
			table=table,
			status="preparing",
		)
		self.authorize_table(table)

		response = self.client.get(
			reverse("order_status", args=[table.number, order.pk]),
		)

		self.assertContains(response, reverse("order_status_data", args=[table.number, order.pk]))
		self.assertContains(response, "window.setInterval(pollOrderStatus, 5000)")
		self.assertContains(response, "updateProgress(data.status)")
		self.assertContains(response, 'data-order-status="ready"')
		self.assertContains(response, "stepIndex < currentIndex || orderIsCompleted")
		self.assertContains(response, "!orderIsCompleted && stepIndex === currentIndex")
		self.assertContains(response, "orderStatus === 'ready' || orderStatus === 'completed'")
		self.assertContains(response, "navigator.vibrate([400, 150, 400, 150, 600])")


def _png(name="promo.png"):
	buffer = io.BytesIO()
	Image.new("RGB", (16, 10), "red").save(buffer, "PNG")
	return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def _marketing_user(username="marketer"):
	user = get_user_model().objects.create_user(username=username, password="password")
	user.groups.add(Group.objects.get_or_create(name="Marketing")[0])
	return user


def _promotion(title, starts_in=timedelta(days=-1), ends_in=timedelta(days=1), **extra):
	now = timezone.now()
	return Promotion.objects.create(
		title=title,
		hero_image=_png(),
		starts_at=now + starts_in,
		ends_at=now + ends_in,
		**extra,
	)


class MarketingAccessTests(TestCase):
	def test_marketing_user_can_log_in_and_reach_promotions(self):
		_marketing_user()

		response = self.client.post(reverse("marketing_login"), {"username": "marketer", "password": "password"})

		self.assertRedirects(response, reverse("marketing_panel"))
		self.assertContains(self.client.get(reverse("marketing_panel")), "Promotions")

	def test_staff_cannot_use_marketing_panel(self):
		staff = get_user_model().objects.create_user(username="cook", password="password", is_staff=True)

		login = self.client.post(reverse("marketing_login"), {"username": "cook", "password": "password"})
		self.assertContains(login, "not a marketing team member")

		self.client.force_login(staff)
		response = self.client.get(reverse("marketing_panel"))
		self.assertRedirects(response, f"{reverse('marketing_login')}?next=%2Fmarketing%2F")

	def test_marketing_cannot_use_staff_panel_or_admin(self):
		self.client.force_login(_marketing_user())

		self.assertNotEqual(self.client.get(reverse("staff_panel")).status_code, 200)
		self.assertNotEqual(self.client.get("/admin/").status_code, 200)

	def test_manager_creates_marketing_user_without_staff_access(self):
		manager = get_user_model().objects.create_superuser(username="boss", password="password")
		self.client.force_login(manager)

		response = self.client.post(reverse("create_staff_user"), {
			"username": "promo-team", "password": "password", "role": "marketing",
		})

		self.assertTrue(response.json()["success"])
		user = get_user_model().objects.get(username="promo-team")
		self.assertFalse(user.is_staff)
		self.assertTrue(user.groups.filter(name="Marketing").exists())
		self.assertContains(self.client.get(reverse("manager_panel")), "promo-team")


class PromotionTests(TestCase):
	def setUp(self):
		self.client.force_login(_marketing_user())

	def test_marketing_creates_promotion_in_samoa_time(self):
		response = self.client.post(reverse("marketing_promotion_create"), {
			"title": "Lunch Stack",
			"badge": "New",
			"hero_image": _png(),
			"price": "15",
			"original_price": "20",
			"starts_at": "2026-10-14T09:00",
			"ends_at": "2026-10-21T21:00",
			"is_published": "on",
			"display_order": "0",
		})

		self.assertRedirects(response, reverse("marketing_panel"))
		promo = Promotion.objects.get(title="Lunch Stack")
		self.assertEqual(promo.savings, 5)
		# 9am in Apia (UTC+13) is 8pm the previous day in UTC.
		self.assertEqual((promo.starts_at.day, promo.starts_at.hour), (13, 20))
		self.assertIsNotNone(promo.created_by)

	def test_end_before_start_is_rejected(self):
		response = self.client.post(reverse("marketing_promotion_create"), {
			"title": "Backwards",
			"hero_image": _png(),
			"starts_at": "2026-10-21T09:00",
			"ends_at": "2026-10-14T09:00",
			"display_order": "0",
		})

		self.assertContains(response, "has to end after it starts")
		self.assertFalse(Promotion.objects.exists())

	def test_promotion_without_duration_is_live(self):
		response = self.client.post(reverse("marketing_promotion_create"), {
			"title": "Always On",
			"hero_image": _png(),
			"is_published": "on",
			"display_order": "0",
		})

		self.assertRedirects(response, reverse("marketing_panel"))
		promo = Promotion.objects.get(title="Always On")
		self.assertIsNone(promo.starts_at)
		self.assertIsNone(promo.ends_at)
		self.assertEqual(promo.status, "live")
		self.assertIn(promo, Promotion.objects.live())
		self.assertContains(self.client.get(reverse("marketing_panel")), "No end date")
		self.assertContains(self.client.get("/"), "Always On")

	def test_toggle_and_delete(self):
		promo = _promotion("Toggle me")

		self.client.post(reverse("marketing_promotion_toggle", args=[promo.pk]))
		promo.refresh_from_db()
		self.assertFalse(promo.is_published)

		self.client.post(reverse("marketing_promotion_delete", args=[promo.pk]))
		self.assertFalse(Promotion.objects.exists())


class LandingPromotionTests(TestCase):
	def test_only_live_published_promotions_show(self):
		_promotion("Live Deal", price="12.50")
		_promotion("Finished Deal", starts_in=timedelta(days=-5), ends_in=timedelta(minutes=-1))
		_promotion("Future Deal", starts_in=timedelta(days=1), ends_in=timedelta(days=3))
		_promotion("Draft Deal", is_published=False)

		response = self.client.get(reverse("index"))

		self.assertContains(response, "Live Deal")
		self.assertContains(response, "<sup>$</sup>12.50", html=False)
		self.assertNotContains(response, "Finished Deal")
		self.assertNotContains(response, "Future Deal")
		self.assertNotContains(response, "Draft Deal")
		self.assertNotContains(response, 'href="/marketing/')

	def test_section_is_absent_without_live_promotions(self):
		response = self.client.get(reverse("index"))

		self.assertNotContains(response, 'id="promotions"')

