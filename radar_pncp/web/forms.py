from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from radar_pncp.config import UFS

from .models import Follow, Preference


class SignupForm(UserCreationForm):
    """Cadastro. O e-mail é obrigatório porque o aviso é o produto.

    Sem endereço, a conta só funciona para quem lembrar de abrir o site — que
    é exatamente o problema que o Radar existe para resolver.
    """

    email = forms.EmailField(
        required=True,
        label="Seu e-mail",
        help_text="Para onde mandamos as oportunidades novas. Não usamos para mais nada.",
    )

    class Meta(UserCreationForm.Meta):
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email


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
