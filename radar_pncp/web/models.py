import re

from django.conf import settings
from django.db import models
from django.utils import timezone


class Market(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    terms = models.JSONField(default=list)
    exclusions = models.JSONField(default=list)

    def __str__(self):
        return self.name


class Preference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.PROTECT)
    uf = models.CharField(max_length=2, blank=True)


class Opportunity(models.Model):
    pncp_id = models.CharField(max_length=100, unique=True)
    title = models.TextField()
    agency = models.CharField(max_length=500)
    uf = models.CharField(max_length=2, blank=True, db_index=True)
    value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    publication_date = models.DateField(null=True, blank=True, db_index=True)
    proposal_opening_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True, db_index=True)
    official_url = models.URLField(max_length=500, blank=True)
    markets = models.ManyToManyField(Market)
    fetched_at = models.DateTimeField()
    plain_summary = models.TextField(blank=True)
    key_points = models.JSONField(default=list, blank=True)
    cautions = models.JSONField(default=list, blank=True)
    summary_model = models.CharField(max_length=100, blank=True)
    summary_source_hash = models.CharField(max_length=64, blank=True)
    summarized_at = models.DateTimeField(null=True, blank=True)
    # Preenchidos sob demanda, no primeiro clique, a partir da rota de item do
    # PNCP: o índice de busca não traz datas de proposta nem valor confiáveis.
    documents = models.JSONField(default=list, blank=True)
    enriched_at = models.DateTimeField(null=True, blank=True)
    enrichment_checked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fetched_at", "pk"]

    @property
    def readable_object(self):
        """Objeto limpo para leitura; o texto oficial continua preservado em `title`."""
        text = re.sub(r"^\[[^]]+\]\s*[-–—:]?\s*", "", self.title).strip()
        letters = [character for character in text if character.isalpha()]
        if letters and sum(character.isupper() for character in letters) / len(letters) > 0.85:
            text = text.capitalize()
        return text

    @property
    def has_official_dates(self):
        """Se as datas vieram da rota de item, e não da vigência do contrato."""
        return self.enriched_at is not None

    @property
    def days_remaining(self):
        if self.deadline is None:
            return None
        return (self.deadline - timezone.localdate()).days


class Alert(models.Model):
    """Registro de que uma oportunidade já foi avisada a alguém.

    Mesma ideia do `estado.py` da CLI: o valor de um radar está em avisar uma
    vez. Repetir o mesmo edital todo dia treina o usuário a ignorar o e-mail,
    e aí a ferramenta morre sem dar erro nenhum.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    opportunity = models.ForeignKey("Opportunity", on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "opportunity")]
        indexes = [models.Index(fields=["user", "sent_at"])]

    def __str__(self):
        return f"{self.user} ← {self.opportunity_id}"


class Follow(models.Model):
    class Stage(models.TextChoices):
        INTERESTED = "interested", "Interessado"
        ANALYZING = "analyzing", "Analisando edital"
        PREPARING = "preparing", "Preparando proposta"
        ARCHIVED = "archived", "Arquivado"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.INTERESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["user", "opportunity"], name="unique_user_opportunity")
        ]
