import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from orders.models import Order
from catalog.models import ProductVariant
from .models import Transaction


def start_payment_view(request, access_token):
    order = get_object_or_404(Order.objects.prefetch_related('items'), access_token=access_token)

    # تعیین اینکه آیا مشتری در حال پرداخت مرحله اول است یا تسویه مابقی بیعانه (مرحله دوم)
    if order.status == Order.StatusChoices.PENDING:
        is_second_stage = False
        amount_toman = order.payable_now

        # بررسی موجودی انبار فقط در مرحله اول (قبل از رزرو لباس)
        for item in order.items.select_related('variant'):
            if not item.variant.is_active or item.variant.stock < item.quantity:
                messages.error(
                    request,
                    f"متاسفانه موجودی «{item.product_name} (سایز {item.size_title})» پیش از پرداخت شما به پایان رسید."
                )
                return redirect('orders:order_summary', access_token=order.access_token)

    elif order.status == Order.StatusChoices.PARTIALLY_PAID and order.remaining_amount > 0:
        is_second_stage = True
        amount_toman = order.remaining_amount
    else:
        return redirect('payments:payment_result', access_token=order.access_token)

    amount_rial = amount_toman * 10

    callback_url = request.build_absolute_uri(
        reverse('payments:verify_payment', kwargs={'access_token': order.access_token})
    )

    stage_desc = "تسویه مابقی" if is_second_stage else "پرداخت"
    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": amount_rial,
        "callback_url": callback_url,
        "description": f"{stage_desc} سفارش {order.order_code} - {order.full_name}",
        "metadata": {
            "mobile": order.phone,
        }
    }

    try:
        response = requests.post(settings.ZARINPAL_REQUEST_URL, json=payload, timeout=12)
        res_data = response.json()
    except requests.RequestException:
        messages.error(request, "خطا در برقراری ارتباط با درگاه زرین‌پال. لطفاً لحظاتی دیگر تلاش کنید.")
        return redirect('orders:order_summary', access_token=order.access_token)

    data = res_data.get('data', {})
    if isinstance(data, dict) and data.get('code') == 100:
        authority = data['authority']
        Transaction.objects.create(
            order=order,
            authority=authority,
            amount_toman=amount_toman,
            is_second_stage=is_second_stage,
            status=Transaction.StatusChoices.PENDING
        )
        return redirect(f"{settings.ZARINPAL_STARTPAY_URL}{authority}")

    errors = res_data.get('errors', {})
    error_code = errors.get('code', 'نامشخص') if isinstance(errors, dict) else 'نامشخص'
    messages.error(request, f"درگاه پرداخت درخواست را نپذیرفت (کد خطا: {error_code}).")
    return redirect('orders:order_summary', access_token=order.access_token)


def verify_payment_view(request, access_token):
    authority = request.GET.get('Authority', '')
    status_param = request.GET.get('Status', '')

    order = get_object_or_404(Order, access_token=access_token)
    tx = get_object_or_404(Transaction, order=order, authority=authority)

    if tx.status == Transaction.StatusChoices.SUCCESS:
        return redirect('payments:payment_result', access_token=order.access_token)

    if status_param != 'OK':
        tx.status = Transaction.StatusChoices.FAILED
        tx.save(update_fields=['status', 'updated_at'])
        return redirect('payments:payment_result', access_token=order.access_token)

    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": tx.amount_toman * 10,
        "authority": authority,
    }

    try:
        response = requests.post(settings.ZARINPAL_VERIFY_URL, json=payload, timeout=12)
        res_data = response.json()
    except requests.RequestException:
        messages.error(request, "ارتباط با بانک جهت تایید تراکنش برقرار نشد. در صورت کسر وجه، مبلغ ظرف ۷۲ ساعت به حساب شما بازمی‌گردد.")
        return redirect('payments:payment_result', access_token=order.access_token)

    data = res_data.get('data', {})
    verify_code = data.get('code') if isinstance(data, dict) else None

    if verify_code in (100, 101):
        with transaction.atomic():
            locked_tx = Transaction.objects.select_for_update().get(pk=tx.pk)
            locked_order = Order.objects.select_for_update().get(pk=order.pk)

            if locked_tx.status != Transaction.StatusChoices.SUCCESS:
                # کسر موجودی انبار فقط در مرحله اول خرید انجام می‌شود
                if not locked_tx.is_second_stage:
                    for item in locked_order.items.all():
                        variant = ProductVariant.objects.select_for_update().get(pk=item.variant_id)
                        variant.stock = max(0, variant.stock - item.quantity)
                        variant.save(update_fields=['stock'])

                locked_tx.status = Transaction.StatusChoices.SUCCESS
                locked_tx.ref_id = str(data.get('ref_id', ''))
                locked_tx.card_pan = str(data.get('card_pan', ''))
                locked_tx.save()

                locked_order.paid_amount += locked_tx.amount_toman
                if locked_order.remaining_amount == 0:
                    locked_order.status = Order.StatusChoices.PAID
                else:
                    locked_order.status = Order.StatusChoices.PARTIALLY_PAID
                locked_order.save()

        return redirect('payments:payment_result', access_token=order.access_token)

    tx.status = Transaction.StatusChoices.FAILED
    tx.save(update_fields=['status', 'updated_at'])
    return redirect('payments:payment_result', access_token=order.access_token)


def payment_result_view(request, access_token):
    order = get_object_or_404(
        Order.objects.prefetch_related('items', 'transactions'),
        access_token=access_token
    )
    latest_tx = order.transactions.first()
    is_paid = latest_tx and latest_tx.status == Transaction.StatusChoices.SUCCESS
    return render(request, 'payments/payment_result.html', {
        'order': order,
        'transaction': latest_tx,
        'is_paid': is_paid,
    })