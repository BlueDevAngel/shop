from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Category, Product


def home_view(request):
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('variants')

    # فیلتر بر اساس دسته‌بندی، تخفیف یا جستجو
    selected_category_slug = request.GET.get('category')
    only_discount = request.GET.get('discount') == '1'
    search_query = request.GET.get('q', '').strip()

    selected_category = None
    if selected_category_slug:
        selected_category = get_object_or_404(Category, slug=selected_category_slug, is_active=True)
        products = products.filter(category=selected_category)

    if only_discount:
        products = products.filter(discount_price__isnull=False)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(fabric_details__icontains=search_query) |
            Q(code__icontains=search_query)
        )

    context = {
        'categories': categories,
        'products': products,
        'selected_category': selected_category,
        'only_discount': only_discount,
        'search_query': search_query,
    }
    return render(request, 'catalog/home.html', context)


def product_detail_view(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images', 'variants'),
        slug=slug,
        is_active=True
    )
    active_variants = product.variants.filter(is_active=True)

    # آماده‌سازی امن داده‌های سایزبندی برای فرانت‌اند (جلوگیری از XSS)
    variants_data = [
        {
            'id': v.id,
            'size_title': v.size_title,
            'price_adjustment': v.price_adjustment,
            'final_price': v.get_final_price(),
            'stock': v.stock,
        }
        for v in active_variants
    ]

    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).prefetch_related('variants')[:4]

    context = {
        'product': product,
        'variants_data': variants_data,
        'related_products': related_products,
    }
    return render(request, 'catalog/product_detail.html', context)