import hashlib
from catalog.models import ProductVariant
from core.models import SiteSetting


class Cart:
    SESSION_KEY = 'boutique_cart'

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(self.SESSION_KEY)
        if not cart:
            cart = self.session[self.SESSION_KEY] = {}
        self.cart = cart

    def _generate_item_key(self, variant_id, custom_measurements=""):
        """ساخت کلید یکتا برای ترکیب سایز + متن اندازه‌های شخصی‌دوزی"""
        clean_note = (custom_measurements or "").strip()
        note_hash = hashlib.md5(clean_note.encode('utf-8')).hexdigest()[:8] if clean_note else "std"
        return f"{variant_id}_{note_hash}"

    def add(self, variant, quantity=1, custom_measurements="", override_quantity=False):
        item_key = self._generate_item_key(variant.id, custom_measurements)
        clean_note = (custom_measurements or "").strip()[:500]  # محدودیت طول امنیتی

        if item_key not in self.cart:
            self.cart[item_key] = {
                'variant_id': variant.id,
                'quantity': 0,
                'custom_measurements': clean_note,
            }

        if override_quantity:
            self.cart[item_key]['quantity'] = max(1, min(quantity, variant.stock))
        else:
            new_qty = self.cart[item_key]['quantity'] + quantity
            self.cart[item_key]['quantity'] = max(1, min(new_qty, variant.stock))

        self.save()

    def remove(self, item_key):
        if item_key in self.cart:
            del self.cart[item_key]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        if self.SESSION_KEY in self.session:
            del self.session[self.SESSION_KEY]
            self.save()

    def __iter__(self):
        variant_ids = [item['variant_id'] for item in self.cart.values()]
        variants = ProductVariant.objects.filter(
            id__in=variant_ids,
            is_active=True,
            product__is_active=True
        ).select_related('product', 'product__category')
        variant_map = {v.id: v for v in variants}

        for item_key, item_data in list(self.cart.items()):
            variant = variant_map.get(item_data['variant_id'])
            if not variant or variant.stock <= 0:
                continue

            # تنظیم خودکار تعداد در صورت کاهش موجودی انبار
            quantity = min(item_data['quantity'], variant.stock)
            unit_price = variant.get_final_price()

            yield {
                'item_key': item_key,
                'variant': variant,
                'product': variant.product,
                'quantity': quantity,
                'custom_measurements': item_data.get('custom_measurements', ''),
                'unit_price': unit_price,
                'total_price': unit_price * quantity,
            }

    def __len__(self):
        return sum(item['quantity'] for item in self.__iter__())

    def get_items_total(self):
        return sum(item['total_price'] for item in self.__iter__())

    def get_shipping_cost(self):
        items_total = self.get_items_total()
        if items_total == 0:
            return 0
        settings_obj = SiteSetting.load()
        if settings_obj.free_shipping_threshold > 0 and items_total >= settings_obj.free_shipping_threshold:
            return 0
        return settings_obj.shipping_cost

    def get_grand_total(self):
        return self.get_items_total() + self.get_shipping_cost()

    def get_deposit_payable(self):
        """محاسبه مبلغ پیش‌پرداخت (درصد بیعانه از جمع لباس‌ها + هزینه ارسال)"""
        settings_obj = SiteSetting.load()
        if not settings_obj.enable_two_stage_payment:
            return self.get_grand_total()
        deposit_items = (self.get_items_total() * settings_obj.deposit_percentage) // 100
        return deposit_items + self.get_shipping_cost()