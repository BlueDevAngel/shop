from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from catalog.models import Category, Product, ProductVariant
from orders.models import Order, OrderItem
from .models import Transaction


class ZarinpalPaymentSecurityTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="کت")
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        img = SimpleUploadedFile("coat.jpg", small_gif, content_type="image/jpeg")
        self.product = Product.objects.create(category=cat, name="کت قهوه‌ای", base_price=4500000, main_image=img)
        self.variant = ProductVariant.objects.create(product=self.product, size_title="40", stock=5)

        self.order = Order.objects.create(
            full_name="تست مشتری",
            phone="09121234567",
            province="تهران",
            city="تهران",
            address="تهران",
            payment_type=Order.PaymentTypeChoices.DEPOSIT,
            items_total=4500000,
            shipping_cost=70000,
            total_amount=4570000,
            payable_now=2320000,
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            variant=self.variant,
            product_name=self.product.name,
            size_title="40",
            unit_price=4500000,
            quantity=1,
        )

    @patch('payments.views.requests.post')
    def test_full_payment_verification_and_stock_deduction(self, mock_post):
        # ۱. شبیه‌سازی درخواست اولیه به زرین‌پال (Request)
        mock_req_response = MagicMock()
        mock_req_response.json.return_value = {
            "data": {"code": 100, "authority": "S00000000000000000000000000000012345"}
        }
        mock_post.return_value = mock_req_response

        res = self.client.get(reverse('payments:start_payment', args=[self.order.access_token]))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Transaction.objects.count(), 1)

        # ۲. شبیه‌سازی بازگشت موفق از بانک و تایید تراکنش (Verify)
        mock_verify_response = MagicMock()
        mock_verify_response.json.return_value = {
            "data": {"code": 100, "ref_id": 987654321, "card_pan": "603799******1234"}
        }
        mock_post.return_value = mock_verify_response

        verify_url = reverse('payments:verify_payment', args=[self.order.access_token])
        self.client.get(f"{verify_url}?Authority=S00000000000000000000000000000012345&Status=OK")

        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        tx = Transaction.objects.first()

        self.assertEqual(tx.status, Transaction.StatusChoices.SUCCESS)
        self.assertEqual(tx.ref_id, "987654321")
        self.assertEqual(self.order.status, Order.StatusChoices.PARTIALLY_PAID)
        self.assertEqual(self.order.paid_amount, 2320000)
        self.assertEqual(self.order.remaining_amount, 2250000)
        # موجودی باید از ۵ به ۴ کاهش یافته باشد
        self.assertEqual(self.variant.stock, 4)

        # ۳. تست امنیت در برابر رفرش دوباره صفحه توسط کاربر (موجودی نباید دوباره کم شود)
        self.client.get(f"{verify_url}?Authority=S00000000000000000000000000000012345&Status=OK")
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 4)
    @patch('payments.views.requests.post')
    def test_second_stage_deposit_settlement_without_double_stock_deduction(self, mock_post):
        """تست پرداخت قسط دوم (تسویه مانده بیعانه) بدون کسر مجدد موجودی انبار"""
        # فرض می‌کنیم مرحله اول پرداخت شده و موجودی از ۵ به ۴ رسیده است
        self.order.status = Order.StatusChoices.PARTIALLY_PAID
        self.order.paid_amount = 2320000
        self.order.save()
        self.variant.stock = 4
        self.variant.save()

        # ۱. درخواست پرداخت مرحله دوم (مابقی مبلغ: 2,250,000 تومان)
        mock_req = MagicMock()
        mock_req.json.return_value = {"data": {"code": 100, "authority": "S00000000000000000000000000000099999"}}
        mock_post.return_value = mock_req

        res = self.client.get(reverse('payments:start_payment', args=[self.order.access_token]))
        self.assertEqual(res.status_code, 302)
        tx2 = Transaction.objects.first()
        self.assertTrue(tx2.is_second_stage)
        self.assertEqual(tx2.amount_toman, 2250000)

        # ۲. تایید پرداخت مرحله دوم
        mock_verify = MagicMock()
        mock_verify.json.return_value = {"data": {"code": 100, "ref_id": 555666777, "card_pan": "603799******9999"}}
        mock_post.return_value = mock_verify

        verify_url = reverse('payments:verify_payment', args=[self.order.access_token])
        self.client.get(f"{verify_url}?Authority=S00000000000000000000000000000099999&Status=OK")

        self.order.refresh_from_db()
        self.variant.refresh_from_db()

        # سفارش باید به وضعیت «تسویه کامل» تغییر کند، مانده صفر شود و موجودی روی همان ۴ بماند
        self.assertEqual(self.order.status, Order.StatusChoices.PAID)
        self.assertEqual(self.order.paid_amount, 4570000)
        self.assertEqual(self.order.remaining_amount, 0)
        self.assertEqual(self.variant.stock, 4)

    def test_smart_order_tracking_by_code_and_phone(self):
        """تست پیگیری هوشمند سفارش با کد سفارش و شماره موبایل"""
        res = self.client.post(reverse('orders:order_track'), {
            'order_code': self.order.order_code,
            'phone': '09121234567'
        })
        self.assertEqual(res.status_code, 302)