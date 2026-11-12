from django.test import Client, TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Category, Product, ProductVariant


class CatalogPricingTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="کت و پالتو")
        # یک تصویر تستی ۱x۱ پیکسل
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        self.dummy_image = SimpleUploadedFile("coat.jpg", small_gif, content_type="image/jpeg")

        self.product = Product.objects.create(
            category=self.category,
            name="کت قهوه‌ای مینسا",
            base_price=4500000,
            fabric_details="آستردار و لمینت شده",
            main_image=self.dummy_image,
            allow_custom_measurements=True
        )

    def test_size_price_adjustment(self):
        """تست افزایش قیمت برای سایزهای بالای ۴۲"""
        v_38 = ProductVariant.objects.create(product=self.product, size_title="38", price_adjustment=0, stock=3)
        v_44 = ProductVariant.objects.create(product=self.product, size_title="44", price_adjustment=350000, stock=2)

        self.assertEqual(v_38.get_final_price(), 4500000)
        self.assertEqual(v_44.get_final_price(), 4850000)
        self.assertEqual(self.product.total_stock, 5)

    def test_discount_and_size_adjustment_combined(self):
        """تست محاسبه همزمان تخفیف محصول و افزایش قیمت سایز"""
        self.product.discount_price = 4000000
        self.product.save()
        v_44 = ProductVariant.objects.create(product=self.product, size_title="44", price_adjustment=350000)
        self.assertEqual(v_44.get_final_price(), 4350000)

    def test_invalid_discount_price_raises_error(self):
        """تخفیف بیشتر یا مساوی قیمت اصلی باید خطا بدهد"""
        self.product.discount_price = 5000000
        with self.assertRaises(ValidationError):
            self.product.full_clean()
    def test_home_page_loads_dynamically(self):
        """تست باز شدن صفحه اصلی و نمایش محصول ثبت شده"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "کت قهوه‌ای مینسا")

    def test_product_detail_page_loads_with_variants(self):
        """تست باز شدن صفحه جزییات محصول و وجود داده‌های سایز"""
        ProductVariant.objects.create(product=self.product, size_title="44", price_adjustment=350000, stock=2)
        response = self.client.get(f'/product/{self.product.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "4850000")


class FavoritesTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name="پوشاک")
        self.product = Product.objects.create(
            category=category, name="کت نمونه ویژه", base_price=1000, main_image="products/main/coat.jpg",
        )
        self.add_url = reverse('catalog:favorite_update', args=[self.product.id, 'add'])
        self.remove_url = reverse('catalog:favorite_update', args=[self.product.id, 'remove'])
        self.list_url = reverse('catalog:favorites')
        self.detail_url = reverse('catalog:product_detail', args=[self.product.slug])

    def test_add_list_and_remove_favorite(self):
        self.assertContains(self.client.get(self.detail_url), "افزودن به علاقه‌مندی‌ها")
        self.client.post(self.add_url, {'next': self.detail_url})
        self.client.post(self.add_url, {'next': self.detail_url})
        self.assertEqual(self.client.session['favorite_products'], [self.product.id])
        self.assertContains(self.client.get(self.list_url), self.product.name)
        self.assertContains(self.client.get(self.detail_url), "حذف از علاقه‌مندی‌ها")
        self.assertContains(self.client.get(reverse('catalog:home')), f'حذف {self.product.name} از علاقه‌مندی‌ها')
        self.client.post(self.remove_url, {'next': self.list_url})
        self.assertNotContains(self.client.get(self.list_url), self.product.name)

    def test_favorites_are_private_to_session_and_hide_inactive_products(self):
        self.client.post(self.add_url)
        self.assertNotContains(Client().get(self.list_url), self.product.name)
        self.product.is_active = False
        self.product.save()
        self.assertNotContains(self.client.get(self.list_url), self.product.name)
        self.assertEqual(self.client.post(self.add_url).status_code, 404)
        self.assertEqual(self.client.post(self.remove_url).status_code, 302)

    def test_updates_require_post_and_csrf_and_reject_external_redirects(self):
        self.assertEqual(self.client.get(self.add_url).status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post(self.add_url).status_code, 403)
        response = self.client.post(self.add_url, {'next': 'https://example.com/'})
        self.assertRedirects(response, self.list_url)
        self.assertEqual(self.client.post(reverse('catalog:favorite_update', args=[self.product.id, 'bad'])).status_code, 404)