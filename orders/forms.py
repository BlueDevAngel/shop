from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'province', 'city', 'address', 'postal_code', 'customer_note', 'payment_type']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full bg-white border border-[#DFD3C7] rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-taupe',
                'placeholder': 'مثال: سارا محمدی'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full bg-white border border-[#DFD3C7] rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-taupe',
                'placeholder': '09123456789',
                'dir': 'ltr'
            }),
            'province': forms.TextInput(attrs={
                'class': 'w-full bg-white border border-[#DFD3C7] rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-taupe',
                'placeholder': 'مثال: تهران'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full bg-white border border-[#DFD3C7] rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-taupe',
                'placeholder': 'مثال: تهران'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full bg-white border border-[#DFD3C7] rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-taupe',
                'rows': 3,
                'placeholder': 'خیابان، کوچه، پلاک، واحد...'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'w-full bg-white border border-[#DFD3C7] rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-taupe',
                'placeholder': 'اختیاری (۱۰ رقم بدون خط تیره)',
                'dir': 'ltr'
            }),
            'customer_note': forms.Textarea(attrs={
                'class': 'w-full bg-white border border-[#DFD3C7] rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-taupe',
                'rows': 2,
                'placeholder': 'اگر نکته خاصی درباره زمان ارسال یا بسته‌بندی دارید بنویسید...'
            }),
        }