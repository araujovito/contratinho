from django.conf import settings
from django.db import models


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
    deadline = models.DateField(null=True, blank=True, db_index=True)
    official_url = models.URLField(max_length=500, blank=True)
    markets = models.ManyToManyField(Market)
    fetched_at = models.DateTimeField()

    class Meta:
        ordering = ["-fetched_at", "pk"]


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
