from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.utils import timezone

class Expediteur(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20)
    ville = models.CharField(max_length=50)
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    email = models.CharField( max_length=50)
class Destinataire(models.Model):
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    email = models.CharField( max_length=50)
    ville = models.CharField(max_length=50)
    def str(self):
       return self.nom

class Colis(models.Model):

    expediteur = models.ForeignKey(Expediteur, on_delete=models.CASCADE)
    destinataire = models.ForeignKey(Destinataire, on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    code_suivi = models.CharField(max_length=100, unique=True)
    adresse = models.TextField()
    description = models.CharField(max_length=255, null=True, blank=True)
    poids = models.FloatField(null=True)
    statut = models.CharField(max_length=50, choices=[
        ('en_attente', 'En attente'),
        ('en_transit', 'En transit'),
        ('livré', 'Livré')
    ])
    date_envoi = models.DateTimeField(auto_now_add=True)

    def str(self):
        return f"{self.code_suivi} - {self.destinataire}"
    

class Notification(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

    def str(self):
        return f"Notification pour {self.utilisateur.username}"



class Article(models.Model):
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    auteur = models.CharField(max_length=100)
    date_publication = models.DateTimeField(default=timezone.now)

    def str(self):
        return self.titre

class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom_complet = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    zone_operation = models.CharField(max_length=100)
    zone_atribuee = models.CharField(max_length=60)
    email = models.CharField( max_length=50)
    def str(self):
        return self.nom_complet
    
class livraison(models.Model):
    id_livraison = models.CharField( max_length=50)
    code_suivi = models.CharField(max_length=100, unique=True) 
    date_livraison = models.DateField(default=timezone.now)
    date_envoi = models.DateField(default=timezone.now)
    Colis = models.ForeignKey(Colis,on_delete=models.CASCADE)
    statut = models.CharField(max_length=50, choices=[
        ('en_attente', 'En attente'),
        ('en_transit', 'En transit'),
        ('livré', 'Livré')
    ])