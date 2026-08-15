import tempfile

from django.contrib.auth import get_user_model
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
	def test_root_opens_staff_panel(self):
		response = self.client.get(reverse("index"))

		self.assertRedirects(response, reverse("staff_panel"), fetch_redirect_response=False)

	def test_signed_out_root_access_reaches_staff_login(self):
		response = self.client.get(reverse("index"), follow=True)

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "menu/staff_login.html")


class OrderItemTests(TestCase):
	def test_string_representation_handles_deleted_menu_item(self):
		order_item = OrderItem(quantity=2, menu_item=None)

		self.assertEqual(str(order_item), "2x Deleted menu item")


class TableQrCodeTests(TestCase):
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
	def test_status_endpoint_returns_live_order_state(self):
		table = Table.objects.create(number=95)
		order = Order.objects.create(
			order_number="ORD-STATUS-TEST",
			table=table,
			status="ready",
		)

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
