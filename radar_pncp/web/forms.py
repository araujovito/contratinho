from django import forms
from django.contrib.auth.forms import UserCreationForm

from radar_pncp.config import UFS

from .models import Follow, Preference


class SignupForm(UserCreationForm):
    pass


class PreferenceForm(forms.ModelForm):
    uf = forms.ChoiceField(
        label="Onde você quer atender?",
        required=False,
        choices=[("", "Todos os estados")] + [(uf, uf) for uf in sorted(UFS)],
    )

    class Meta:
        model = Preference
        fields = ["market", "uf"]
        labels = {"market": "Qual é o seu mercado?"}


class FollowForm(forms.ModelForm):
    class Meta:
        model = Follow
        fields = ["stage"]
        labels = {"stage": "Etapa do acompanhamento"}
