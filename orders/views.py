from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import transaction
from catalog.models import ProductVariant
from core.models import SiteSetting
from .cart import Cart
from .models import Order, OrderItem
from .forms import CheckoutForm


def _save_order_to_session(request, order):
    """ذخیره خودکار سفارش در حافظه مرورگر مشتری برای پیگیری راحت بدون لاگین"""
    recent = request.session.get('recent_order_tokens', [])
    token_str = str(order.access_token)
    if token_str not in recent:
        recent.insert(0, token_str)
        request.session['recent_order_tokens'] = recent[:10]
        request.session.modified = True


@require_POST
def cart_add_view(request):
    cart = Cart(request)
    variant_id = request.POST.get('variant_id')
    custom_measurements = request.POST.get('custom_measurements', '').strip()

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    variant = get_object_or_404(
        ProductVariant.objects.select_related('product'),
        id=variant_id,
        is_active=True,
        product__is_active=True
    )

    if variant.stock <= 0:
        messages.error(request, "متاسفانه موجودی این سایز به پایان رسیده است.")
        return redirect('catalog:product_detail', slug=variant.product.slug)

    if not variant.product.allow_custom_measurements:
        custom_measurements = ""

    cart.add(variant=variant, quantity=quantity, custom_measurements=custom_measurements)
    messages.success(request, f"«{variant.product.name} (سایز {variant.size_title})» به سبد خرید اضافه شد.")
    return redirect('orders:cart_detail')


@require_POST
def cart_update_view(request, item_key):
    cart = Cart(request)
    if item_key in cart.cart:
        variant_id = cart.cart[item_key]['variant_id']
        custom_measurements = cart.cart[item_key].get('custom_measurements', '')
        variant = get_object_or_404(ProductVariant, id=variant_id, is_active=True)
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1

        if quantity <= 0:
            cart.remove(item_key)
        else:
            cart.add(variant=variant, quantity=quantity, custom_measurements=custom_measurements, override_quantity=True)
    return redirect('orders:cart_detail')


@require_POST
def cart_remove_view(request, item_key):
    cart = Cart(request)
    cart.remove(item_key)
    messages.info(request, "محصول از سبد خرید حذف شد.")
    return redirect('orders:cart_detail')


def cart_detail_view(request):
    cart = Cart(request)
    return render(request, 'orders/cart_detail.html', {'cart': cart})


def checkout_view(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "سبد خرید شما خالی است.")
        return redirect('catalog:home')

    site_settings = SiteSetting.load()

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)

                items_total = cart.get_items_total()
                shipping_cost = cart.get_shipping_cost()
                grand_total = items_total + shipping_cost

                if not site_settings.enable_two_stage_payment:
                    order.payment_type = Order.PaymentTypeChoices.FULL

                order.items_total = items_total
                order.shipping_cost = shipping_cost
                order.total_amount = grand_total

                if order.payment_type == Order.PaymentTypeChoices.DEPOSIT:
                    order.payable_now = cart.get_deposit_payable()
                else:
                    order.payable_now = grand_total

                order.save()

                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        variant=item['variant'],
                        product_name=item['product'].name,
                        size_title=item['variant'].size_title,
                        unit_price=item['unit_price'],
                        quantity=item['quantity'],
                        custom_measurements=item['custom_measurements'],
                    )

                cart.clear()
                _save_order_to_session(request, order)
                return redirect('orders:order_summary', access_token=order.access_token)
    else:
        form = CheckoutForm(initial={'payment_type': Order.PaymentTypeChoices.FULL})

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'form': form,
    })


def order_summary_view(request, access_token):
    order = get_object_or_404(Order.objects.prefetch_related('items', 'transactions'), access_token=access_token)
    return render(request, 'orders/order_summary.html', {'order': order})


def order_track_view(request):
    """جستجوی هوشمند سفارش با کد سفارش + شماره موبایل و نمایش سفارش‌های اخیر مرورگر"""
    # تبدیل اعداد فارسی احتمالی به انگلیسی
    persian_to_eng = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')

    if request.method == 'POST':
        raw_code = request.POST.get('order_code', '').strip().translate(persian_to_eng).upper()
        raw_phone = request.POST.get('phone', '').strip().translate(persian_to_eng)

        if raw_code and not raw_code.startswith('MN-'):
            raw_code = f"MN-{raw_code}"

        order = Order.objects.filter(order_code__iexact=raw_code, phone=raw_phone).first()
        if order:
            _save_order_to_session(request, order)
            return redirect('orders:order_summary', access_token=order.access_token)
        else:
            messages.error(request, "سفارشی با این کد و شماره موبایل یافت نشد. لطفاً اطلاعات را بررسی کنید.")

    recent_tokens = request.session.get('recent_order_tokens', [])
    recent_orders = Order.objects.filter(access_token__in=recent_tokens).prefetch_related('items')

    return render(request, 'orders/order_track.html', {
        'recent_orders': recent_orders,
    })


@staff_member_required
def shipping_label_view(request, access_token):
    """صفحه مخصوص مدیر فروشگاه جهت چاپ برچسب پستی و جزئیات دوخت سفارش"""
    order = get_object_or_404(Order.objects.prefetch_related('items'), access_token=access_token)
    return render(request, 'orders/shipping_label.html', {'order': order})