from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

# Modèle Utilisateur personnalisé (pour centraliser agents, expéditeurs, destinataires)
class Utilisateur(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    role = models.CharField(
        max_length=50,
        choices=[('agent', 'Agent'), ('expediteur', 'Expéditeur'), ('destinataire', 'Destinataire')],
        default='agent'
    )
    date_creation = models.DateTimeField(default=timezone.now)

    # Add related_name to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='utilisateur_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='utilisateur_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

class Expediteur(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    qr_code = models.CharField(max_length=100, unique=True, blank=True)
    date_creation = models.DateTimeField(default=timezone.now)
    telephone = models.CharField(max_length=20)
    ville = models.CharField(max_length=50)
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    email = models.CharField( max_length=50)
    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.qr_code = str(uuid.uuid4())  # Génère un identifiant unique pour le QR code
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Expéditeur"
        verbose_name_plural = "Expéditeurs"   

class Destinataire(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    email = models.CharField( max_length=50)
    ville = models.CharField(max_length=50)
    qr_code = models.CharField(max_length=100, unique=True, blank=True)
    date_creation = models.DateTimeField(default=timezone.now)


    def str(self):
       return self.nom
    
    class Meta:
        verbose_name = "Destinataire"
        verbose_name_plural = "Destinataires"

class Colis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediteur = models.ForeignKey(Expediteur, on_delete=models.CASCADE)
    destinataire = models.ForeignKey(Destinataire, on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    code_suivi = models.CharField(max_length=100, unique=True)
    adresse = models.TextField()
    description = models.TextField(null= True)
    poids = models.FloatField(null=True)
    statut = models.CharField(max_length=50, choices=[
        ('en_attente', 'En attente'),
        ('en_transit', 'En transit'),
        ('livré', 'Livré')
    ])
    date_envoi = models.DateTimeField(auto_now_add=True)
    date_creation = models.DateTimeField(default=timezone.now)
    def str(self):
        return f"{self.code_suivi} - {self.destinataire} - {expediteur}"
    class Meta:
        verbose_name = "Colis"
        verbose_name_plural = "Colis"
    

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

   
    def __str__(self):
        return f"Notification pour {self.utilisateur.username}: {self.message[:50]}"

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-date']  # Trier par date descendante


class Article(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Nouvelle clé primaire
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='articles')
    date_publication = models.DateTimeField(default=timezone.now)

    def str(self):
        return self.titre
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-date_publication']

class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom_complet = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    zone_operation = models.CharField(max_length=100)
    zone_atribuee = models.CharField(max_length=60)
    email = models.CharField( max_length=50)
    mot_de_passe = models.CharField(max_length=128, null=True)  # Doit être haché dans la pratique
    def str(self):
        return self.nom_complet
    class Meta:
        verbose_name = "Agent"
        verbose_name_plural = "Agents"
    
class Livraison(models.Model):
    id_livraison = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_suivi = models.CharField(max_length=100, unique=True) 
    date_livraison = models.DateField(default=timezone.now)
    date_envoi = models.DateField(default=timezone.now)
    Colis = models.ForeignKey(Colis,on_delete=models.CASCADE)
    statut = models.CharField(max_length=50, choices=[
        ('en_attente', 'En attente'),
        ('en_transit', 'En transit'),
        ('livré', 'Livré')
    ])
    def save(self, *args, **kwargs):
        if not self.code_suivi:
            self.code_suivi = f"LIV-{uuid.uuid4().hex[:8].upper()}"  # Génère un code de suivi unique
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Livraison {self.code_suivi} pour Colis {self.colis.id}"

    class Meta:
        verbose_name = "Livraison"
        verbose_name_plural = "Livraisons"
        ordering = ['-date_envoi']

class EnregistrementScan(models.Model):
    TYPE_SCAN_CHOICES = [
        ('identification', 'Identification'),
        ('livraison', 'Livraison'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    colis = models.ForeignKey(Colis, on_delete=models.CASCADE, related_name='scans')
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='scans')
    qr_expediteur = models.CharField(max_length=100)
    qr_destinataire = models.CharField(max_length=100)
    type_scan = models.CharField(max_length=20, choices=TYPE_SCAN_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    resultat = models.CharField(max_length=100, default='Succès')

    def __str__(self):
        return f"Scan {self.colis} par {self.agent} à {self.timestamp}"

    class Meta:
        verbose_name = "Enregistrement de Scan"
        verbose_name_plural = "Enregistrements de Scan"






class DemandeInfos(models.Model):
    nom = models.CharField(max_length=150)
    email = models.EmailField()
    telephone = models.CharField(max_length=30)
    adresse = models.CharField(max_length=255)
    description_colis = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Demande d'informations"
        verbose_name_plural = "Demandes d'informations"

    def __str__(self):
        return f"{self.nom} — {self.telephone}"
