
# Project: White-Label E-Commerce (Django 5 + Tailwind CSS + Zarinpal)

## Core Rules
- **No Hardcoding**: Never hardcode brand names, logos, phone numbers, shipping costs, or Instagram links. Always read from `site_settings` context processor (`core.models.SiteSetting`).
- **Tech Stack**: Python/Django 5, SQLite (dev) / PostgreSQL (prod), Tailwind CSS (RTL Persian layout, `dir="rtl"`, Vazirmatn font). Keep JS minimal (vanilla JS or Alpine.js only when necessary).
- **Security First**:
  - Never trust client-side prices or quantities. Always compute totals inside model methods or server-side services using `Decimal`.
  - Use `transaction.atomic()` and `select_for_update()` for stock deduction and payment verification.
  - Read all secrets (`SECRET_KEY`, `ZARINPAL_MERCHANT_ID`, `ADMIN_URL`) via `python-decouple`.
- **UI Guidelines**: Mobile-first, clean minimalist luxury clothing store aesthetic. Generate complete, ready-to-use Django HTML templates with Tailwind classes since the developer works strictly in Python.
- **Admin UX**: Customize `admin.py` using `TabularInline`, `list_display`, `list_editable`, and Persian `verbose_name` so a non-technical store owner can manage everything easily.