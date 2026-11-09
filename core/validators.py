import os
from django.core.exceptions import ValidationError

def validate_image_security(file):
    # ۱. بررسی حجم فایل (حداکثر ۵ مگابایت)
    max_size_mb = 5
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"حجم تصویر نباید بیشتر از {max_size_mb} مگابایت باشد.")
    
    # ۲. بررسی پسوند مجاز
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError("فرمت فایل مجاز نیست. لطفاً فقط عکس با فرمت JPG، PNG یا WEBP آپلود کنید.")