from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager
from django.utils import timezone
from django.conf import settings
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

# =============================
# Utilisateur personnalisé
# =============================
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ("expediteur", "Expéditeur"),
        ("agent", "Agent"),
        ("transporteur", "Transporteur"),
        ("admin", "Administrateur"),
    )
    role = models.CharField(  # Ajout du champ manquant
        max_length=50,
        choices=[
            ('agent', 'Agent'),
            ('expediteur', 'Expéditeur'),
            ('destinataire', 'Destinataire')
        ],
        default='expediteur'
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default="expediteur")
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)

    # On utilise l'email comme identifiant de connexion
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # username reste obligatoire à la création via createsuperuser
    objects = CustomUserManager()

    def __str__(self):
        return self.email
    class Meta:
        verbose_name = "CustomUser"
        verbose_name_plural = "CustomUser"


# =============================
# Entités métier
# =============================
class Expediteur(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='expediteur')
    entreprise = models.CharField(max_length=100, blank=True, null=True)
    qr_code = models.CharField(max_length=100, unique=True, blank=True)
    date_inscription = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    date_creation = models.DateTimeField(default=timezone.now)

    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    email = models.EmailField(max_length=254)
    ville = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.qr_code = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Expéditeur - {self.user.email}"

    class Meta:
        verbose_name = "Expéditeur"
        verbose_name_plural = "Expéditeurs"


class Destinataire(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom_complet = models.CharField(max_length=200, null=True)
    telephone = models.CharField(max_length=20)
    email = models.EmailField(max_length=254)
    ville = models.CharField(max_length=50)
    code_postal = models.CharField(max_length=10, blank=True, null=True)
    qr_code = models.CharField(max_length=100, unique=True, blank=True)
    date_creation = models.DateTimeField(default=timezone.now)
    adresse = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nom_complet or "Destinataire"

    class Meta:
        verbose_name = "Destinataire"
        verbose_name_plural = "Destinataires"
    def save(self, *args, **kwargs):
        if not self.qr_code:
            # Génère un QR code unique basé sur uuid
            self.qr_code = str(uuid.uuid4())
        super().save(*args, **kwargs)


class Agent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profil_agent")
    nom_complet = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    zone_operation = models.CharField(max_length=100)
    zone_attribuee = models.CharField(max_length=60)
    email = models.EmailField(max_length=254)
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agent",
        null=True
    )

    def __str__(self):
        return f"Agent - {self.user.email}"

    class Meta:
        verbose_name = "Agent"
        verbose_name_plural = "Agents"


class Transporteur(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profil_transporteur")
    entreprise = models.CharField(max_length=100, blank=True)
    capacite = models.PositiveIntegerField(default=0)
    est_disponible = models.BooleanField(default=True)
    nom = models.CharField(max_length=100, null=True,blank=True)
    telephone = models.PositiveIntegerField(null=True, blank=True)
    vehicule = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    def __str__(self):
        return f"Transporteur - {self.user.email}"


class Colis(models.Model):
    STATUT_CHOICES = (
        ("enregistre", "Enregistré"),
        ("en_transit", "En transit"),
        ("en_livraison", "En livraison"),
        ("livre", "Livré"),
        ("probleme", "Problème"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediteur = models.ForeignKey(Expediteur, on_delete=models.CASCADE, related_name="colis_envoyes")
    destinataire = models.ForeignKey(Destinataire, on_delete=models.CASCADE, related_name="colis_recus")
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name="colis")
    transporteur = models.ForeignKey(Transporteur, on_delete=models.SET_NULL, null=True, blank=True, related_name="colis")
    utilisateur = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        related_name="colis"
    )
    # utilisateur qui a créé l'enregistrement (peut dupliquer info avec expediteur.user, mais utile pour l'audit)
    # utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="colis_crees")

    code_suivi = models.CharField(max_length=100, unique=True, blank=True)
    adresse = models.TextField()
    description = models.TextField(null=True, blank=True)
    poids = models.FloatField(null=True, blank=True)
    dimensions = models.CharField(max_length=50, blank=True)
    valeur = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="enregistre")
    date_envoi = models.DateTimeField(auto_now_add=True)
    date_creation = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.code_suivi:
            self.code_suivi = f"PKG-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Colis {self.id} - {self.destinataire}"

    class Meta:
        verbose_name = "Colis"
        verbose_name_plural = "Colis"


class Tache(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    colis = models.ForeignKey(Colis, on_delete=models.CASCADE, related_name="taches")
    transporteur = models.ForeignKey(Transporteur, on_delete=models.CASCADE, related_name="taches")
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="taches")
    date_attribution = models.DateTimeField(auto_now_add=True)
    date_livraison_prevue = models.DateTimeField()
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[('pending', 'En attente'), ('in_progress', 'En cours'), ('done', 'Terminé')],null=True,blank=True)
    def __str__(self):
        return f"Tâche de {self.agent} pour {self.transporteur}"


class Notification(models.Model):
    class Channel(models.TextChoices):
        IN_APP = "IN_APP", "In-app"
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"

    TYPE_CHOICES = (
        ("nouveau_colis", "Nouveau colis"),
        ("validation_agent", "Validation agent"),
        ("livraison", "Livraison"),
        ("autre", "Autre"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    type_notification = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True)
    canal = models.CharField(max_length=20, choices=Channel.choices, default=Channel.IN_APP)
    meta = models.JSONField(blank=True, null=True)

    message = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

    def __str__(self):
        username = self.destinataire.username if self.destinataire else "(anonyme)"
        type_label = dict(self.TYPE_CHOICES).get(self.type_notification or "autre", "Autre")
        return f"{type_label} - {username}"

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-date"]


class Article(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="articles")
    date_publication = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.titre

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ["-date_publication"]


class Livraison(models.Model):
    id_livraison = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    colis = models.ForeignKey(Colis, on_delete=models.CASCADE, related_name="livraisons",null=True,blank=True)
    code_suivi = models.CharField(max_length=100, unique=True, blank=True)
    date_livraison = models.DateField(default=timezone.now)
    date_envoi = models.DateField(default=timezone.now)
    statut = models.CharField(
        max_length=50,
        choices=[
            ("en_attente", "En attente"),
            ("en_transit", "En transit"),
            ("livre", "Livré"),
        ],
        default="en_attente",
    )

    def save(self, *args, **kwargs):
        if not self.code_suivi:
            self.code_suivi = f"LIV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Livraison {self.code_suivi} pour Colis {self.colis.code_suivi}"

    class Meta:
        verbose_name = "Livraison"
        verbose_name_plural = "Livraisons"
        ordering = ["-date_envoi"]


class EnregistrementScan(models.Model):
    TYPE_SCAN_CHOICES = [
        ("identification", "Identification"),
        ("livraison", "Livraison"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    colis = models.ForeignKey(Colis, on_delete=models.CASCADE, related_name="scans")
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="scans")
    qr_expediteur = models.CharField(max_length=100)
    qr_destinataire = models.CharField(max_length=100)
    type_scan = models.CharField(max_length=20, choices=TYPE_SCAN_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    resultat = models.CharField(max_length=100, default="Succès")

    def __str__(self):
        return f"Scan {self.colis.code_suivi} par {self.agent.nom_complet} à {self.timestamp:%Y-%m-%d %H:%M}"

    class Meta:
        verbose_name = "Enregistrement de Scan"
        verbose_name_plural = "Enregistrements de Scan"


class DemandeInfos(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=150)
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="demandes_info",
        null=True,
        blank=True,
    )
    email = models.EmailField()
    telephone = models.CharField(max_length=30)
    adresse = models.CharField(max_length=255)
    description_colis = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    reponse = models.TextField(blank=True, null=True)
    repondu = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nom} — {self.telephone}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Demande d'informations"
        verbose_name_plural = "Demandes d'informations"
