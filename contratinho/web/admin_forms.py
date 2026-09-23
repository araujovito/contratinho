from django import forms
from django.utils import timezone

from .models import Market, Opportunity


class TermsField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", forms.Textarea(attrs={"rows": 3}))
        kwargs.setdefault("help_text", "Separe os termos com vírgulas.")
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, list):
            return ", ".join(value)
        return value

    def to_python(self, value):
        value = super().to_python(value)
        return [item.strip() for item in value.split(",") if item.strip()]


class MarketAdminForm(forms.ModelForm):
    terms = TermsField(label="Termos procurados")
    exclusions = TermsField(label="Termos ignorados", required=False)

    class Meta:
        model = Market
        fields = ["name", "slug", "terms", "exclusions"]
        labels = {"name": "Nome", "slug": "Identificador"}


class OpportunityAdminForm(forms.ModelForm):
    official_url = forms.URLField(
        label="Link oficial",
        required=False,
        assume_scheme="https",
    )

    class Meta:
        model = Opportunity
        fields = [
            "pncp_id",
            "title",
            "agency",
            "uf",
            "value",
            "publication_date",
            "proposal_opening_date",
            "deadline",
            "official_url",
            "markets",
        ]
        labels = {
            "pncp_id": "Identificador PNCP",
            "title": "Objeto da oportunidade",
            "agency": "Órgão",
            "uf": "UF",
            "value": "Valor estimado",
            "publication_date": "Data de publicação",
            "proposal_opening_date": "Abertura das propostas",
            "deadline": "Encerramento",
            "official_url": "Link oficial",
            "markets": "Mercados relacionados",
        }
        widgets = {
            "title": forms.Textarea(
                attrs={
                    "rows": 9,
                    "class": "opportunity-object-input",
                    "aria-describedby": "object-reading-help",
                }
            ),
            "publication_date": forms.DateInput(attrs={"type": "date"}),
            "proposal_opening_date": forms.DateInput(attrs={"type": "date"}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "markets": forms.CheckboxSelectMultiple(),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.fetched_at:
            instance.fetched_at = timezone.now()
        if commit:
            instance.save()
            self.save_m2m()
        return instance
