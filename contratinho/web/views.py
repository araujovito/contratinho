from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from contratinho.filtro import termos_encontrados

from . import documentos
from .forms import FollowForm, PreferenceForm, SignupForm
from .models import Follow, Opportunity, Preference


def home(request):
    return render(request, "contratinho/home.html")


def signup(request):
    if request.user.is_authenticated:
        return redirect("preferences")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("preferences")
    return render(
        request,
        "contratinho/form.html",
        {"form": form, "title": "Crie sua conta", "button": "Criar conta"},
    )


@login_required
def preferences(request):
    current = Preference.objects.filter(user=request.user).first()
    form = PreferenceForm(request.POST or None, instance=current)
    if request.method == "POST" and form.is_valid():
        preference = form.save(commit=False)
        preference.user = request.user
        preference.save()
        return redirect("opportunities")
    return render(
        request,
        "contratinho/form.html",
        {"form": form, "title": "Seu mercado, suas oportunidades", "button": "Salvar interesses"},
    )


@login_required
def opportunities(request):
    preference = Preference.objects.select_related("market").filter(user=request.user).first()
    if not preference:
        return redirect("preferences")
    items = Opportunity.objects.filter(markets=preference.market).filter(
        Q(deadline__gte=timezone.localdate()) | Q(deadline__isnull=True)
    )
    if preference.uf:
        items = items.filter(uf=preference.uf)
    page = Paginator(items, 20).get_page(request.GET.get("page"))
    followed = set(
        Follow.objects.filter(user=request.user, opportunity__in=page.object_list).values_list(
            "opportunity_id", flat=True
        )
    )
    for item in page.object_list:
        item.match_terms = termos_encontrados(item.title, preference.market.terms)
    return render(
        request,
        "contratinho/opportunities.html",
        {"page": page, "preference": preference, "followed": followed},
    )


@login_required
def detail(request, pk):
    item = get_object_or_404(Opportunity, pk=pk)
    # O índice de busca não traz datas de proposta nem os anexos. Buscamos o
    # dado oficial no primeiro clique: é aqui que o usuário decide, e é o único
    # momento em que uma consulta por edital se paga.
    if documentos.precisa_enriquecer(item):
        documentos.enriquecer(item)
    follow = Follow.objects.filter(user=request.user, opportunity=item).first()
    preference = Preference.objects.select_related("market").filter(user=request.user).first()
    match_terms = termos_encontrados(item.title, preference.market.terms) if preference else ()
    return render(
        request,
        "contratinho/detail.html",
        {"item": item, "follow": follow, "match_terms": match_terms},
    )


@login_required
@require_POST
def follow(request, pk):
    item = get_object_or_404(Opportunity, pk=pk)
    Follow.objects.get_or_create(user=request.user, opportunity=item)
    return redirect("following")


@login_required
def following(request):
    items = Follow.objects.filter(user=request.user).select_related("opportunity")
    return render(
        request,
        "contratinho/following.html",
        {"page": Paginator(items, 20).get_page(request.GET.get("page"))},
    )


@login_required
def update_follow(request, pk):
    item = get_object_or_404(Follow, pk=pk, user=request.user)
    form = FollowForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Etapa atualizada.")
        return redirect("following")
    return render(
        request,
        "contratinho/form.html",
        {"form": form, "title": "Organize sua participação", "button": "Salvar etapa"},
    )


@login_required
@require_POST
def unfollow(request, pk):
    item = get_object_or_404(Follow, pk=pk, user=request.user)
    item.delete()
    return redirect("following")
