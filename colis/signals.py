# mon_app/signals.py
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DemandeInfos
from .models import CustomUser, Agent

@receiver(post_save, sender=DemandeInfos)
def envoyer_email_demande(sender, instance: DemandeInfos, created, **kwargs):
    if not created:
        return
    sujet = "Nouvelle demande d'informations - Gestion de colis"
    corps = (
        f"Nom: {instance.nom}\n"
        f"Email: {instance.email}\n"
        f"Téléphone: {instance.telephone}\n"
        f"Adresse: {instance.adresse}\n\n"
        f"Description du colis:\n{instance.description_colis}\n\n"
        f"Reçue le: {instance.created_at}"
    )
    destinataire = getattr(settings, "EMAIL_DESTINATAIRE_ENTREPRISE", "medonjiojodeanas@gmail.com")
    try:
        send_mail(sujet, corps, settings.DEFAULT_FROM_EMAIL, [destinataire], fail_silently=True)
    except Exception:
        # En dev on ignore ; en prod logguer l'erreur
        pass

@receiver(post_save, sender=CustomUser)
def create_agent_for_user(sender, instance, created, **kwargs):
    if created and instance.role == "agent":  # Si tu as un champ "role"
        Agent.objects.create(utilisateur=instance)
