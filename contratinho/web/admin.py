from django.contrib import admin

from .models import Follow, Market, Opportunity, Preference


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ("pncp_id", "agency", "uf", "deadline", "fetched_at")
    list_filter = ("uf", "markets")
    search_fields = ("pncp_id", "title", "agency")
    filter_horizontal = ("markets",)


@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "market", "uf")
    list_filter = ("market", "uf")
    search_fields = ("user__username",)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("user", "opportunity", "stage", "created_at")
    list_filter = ("stage",)
    search_fields = ("user__username", "opportunity__title")
