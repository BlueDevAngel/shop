from django import template

register = template.Library()

PERSIAN_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')

@register.filter(name='toman')
def toman(value):
    """تبدیل عدد به فرمت سه‌رقمی با ارقام فارسی (مثال: ۴,۵۰۰,۰۰۰)"""
    try:
        value = int(value)
        formatted = f"{value:,}"
        return formatted.translate(PERSIAN_DIGITS)
    except (ValueError, TypeError):
        return value

@register.filter(name='fa_digits')
def fa_digits(value):
    """تبدیل هر رشته حاوی عدد به ارقام فارسی"""
    if value is None:
        return ""
    return str(value).translate(PERSIAN_DIGITS)