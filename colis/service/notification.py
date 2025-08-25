from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from ..models import Notification

def notify_user(user: User, titre: str, message: str, type_="SYSTEM", canal="IN_APP", meta=None, send_email=False):
    notif = Notification.objects.create(
        utilisateur=user, titre=titre, message=message, type=type_, canal=canal, meta=meta or {}
    )
    if send_email:
        # Assure-toi d'avoir configuré EMAIL_BACKEND et DEFAULT_FROM_EMAIL
        try:
            send_mail(
                subject=titre,
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass
    return notif

def notify_colis_creation(colis, actor: User):
    # notifie le créateur
    if actor:
        notify_user(
            actor,
            titre=f"Colis {colis.code} enregistré",
            message=f"Votre colis {colis.code} a été créé avec succès.",
            type_="COLIS",
            meta={"colis_id": colis.id, "code": colis.code},
        )
    # notifie l'agent assigné
    if colis.assigned_agent:
        notify_user(
            colis.assigned_agent,
            titre=f"Nouveau colis assigné: {colis.code}",
            message=f"Vous avez été assigné au colis {colis.code}.",
            type_="COLIS",
            meta={"colis_id": colis.id, "code": colis.code},
        )

def notify_livraison_update(livraison, actor: User = None):
    code = livraison.colis.code
    # notifie le créateur du colis s'il existe
    if livraison.colis.created_by:
        notify_user(
            livraison.colis.created_by,
            titre=f"Livraison {code}: {livraison.statut}",
            message=f"Le statut de la livraison du colis {code} est passé à {livraison.statut}.",
            type_="LIVRAISON",
            meta={"colis_id": livraison.colis.id, "code": code, "livraison_id": livraison.id},
        )
    # notifie le livreur
    if livraison.livreur:
        notify_user(
            livraison.livreur,
            titre=f"Mission mise à jour: {code}",
            message=f"Le colis {code} est maintenant au statut {livraison.statut}.",
            type_="LIVRAISON",
            meta={"colis_id": livraison.colis.id, "code": code, "livraison_id": livraison.id},
        )

def notify_demande_info(demande):
    # notifie un staff (ex: superusers) ou l'agent assigné si disponible
    if demande.colis.assigned_agent:
        notify_user(
            demande.colis.assigned_agent,
            titre=f"Nouvelle demande d'info sur {demande.colis.code}",
            message=f"Question: {demande.question[:120]}",  # noqa
            type_="INFO",
            meta={"colis_id": demande.colis.id, "demande_id": demande.id},
        )
    else:
        for admin in User.objects.filter(is_staff=True):
            notify_user(
                admin,
                titre=f"Nouvelle demande d'info sur {demande.colis.code}",
                message=f"Question: {demande.question[:120]}",  # noqa
                type_="INFO",
                meta={"colis_id": demande.colis.id, "demande_id": demande.id},
            )

def notify_reponse_info(demande):
    notify_user(
        demande.auteur,
        titre=f"Réponse à votre demande sur {demande.colis.code}",
        message=f"Réponse: {demande.reponse}",
        type_="INFO",
        meta={"colis_id": demande.colis.id, "demande_id": demande.id},
        send_email=True  # active si tu veux un email
    )
