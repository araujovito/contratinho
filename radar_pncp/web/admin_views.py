from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .admin_forms import MarketAdminForm, OpportunityAdminForm
from .models import Follow, Market, Opportunity

staff_required = user_passes_test(lambda user: user.is_active and user.is_staff)


@staff_required
def dashboard(request):
    context = {
        "section": "dashboard",
        "market_count": Market.objects.count(),
        "opportunity_count": Opportunity.objects.count(),
        "user_count": get_user_model().objects.exclude(username="admin-local").count(),
        "follow_count": Follow.objects.count(),
        "latest": Opportunity.objects.prefetch_related("markets")[:5],
        "markets": Market.objects.annotate(total=Count("opportunity"))[:6],
    }
    return render(request, "management/dashboard.html", context)


@staff_required
def markets(request):
    items = Market.objects.annotate(
        opportunity_count=Count("opportunity", distinct=True),
        preference_count=Count("preference", distinct=True),
    ).order_by("name")
    return render(
        request,
        "management/markets.html",
        {"section": "markets", "items": items},
    )


@staff_required
def market_edit(request, pk=None):
    item = get_object_or_404(Market, pk=pk) if pk else None
    form = MarketAdminForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, f"Mercado “{saved.name}” salvo.")
        return redirect("admin_markets")
    return render(
        request,
        "management/form.html",
        {
            "section": "markets",
            "title": "Editar mercado" if item else "Novo mercado",
            "description": "Defina palavras que aproximam as oportunidades deste mercado.",
            "form": form,
            "back_url": "admin_markets",
        },
    )


@staff_required
def opportunities(request):
    query = request.GET.get("q", "").strip()
    items = Opportunity.objects.prefetch_related("markets")
    if query:
        items = items.filter(
            Q(title__icontains=query) | Q(agency__icontains=query) | Q(pncp_id__icontains=query)
        )
    page = Paginator(items, 25).get_page(request.GET.get("page"))
    return render(
        request,
        "management/opportunities.html",
        {"section": "opportunities", "page": page, "query": query},
    )


@staff_required
def opportunity_edit(request, pk=None):
    item = get_object_or_404(Opportunity, pk=pk) if pk else None
    form = OpportunityAdminForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Oportunidade salva.")
        return redirect("admin_opportunities")
    return render(
        request,
        "management/form.html",
        {
            "section": "opportunities",
            "title": "Editar oportunidade" if item else "Nova oportunidade",
            "description": "Revise os dados exibidos no catálogo público.",
            "form": form,
            "back_url": "admin_opportunities",
        },
    )


@staff_required
def users(request):
    items = (
        get_user_model()
        .objects.exclude(username="admin-local")
        .select_related("preference__market")
        .annotate(follow_count=Count("follow"))
        .order_by("-date_joined")
    )
    return render(
        request,
        "management/users.html",
        {"section": "users", "items": items},
    )
