from django.shortcuts import render


def rules_view(request):
    return render(request, 'core/rules.html')