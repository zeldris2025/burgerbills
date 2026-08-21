import tempfile

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Order, OrderItem, Table


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
