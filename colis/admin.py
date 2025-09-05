from django.contrib import admin
from .models import Agent
from .models import CustomUser
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User, Group
# Register your models here.
from django.contrib import admin
from .models import Expediteur,Destinataire,Colis,Notification,Article,Agent,Livraison,EnregistrementScan,CustomUser,Transporteur,Tache
# Register your models here.
admin.site.register(Expediteur)
class ExpediteurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'telephone')
    search_fields = ('nom', 'email')
    list_filter = ('ville',)
    ordering = ('nom',)

admin.site.register(Livraison)
class LivraisonAdmin(admin.ModelAdmin):
    list_display = ('colis', 'date_envoi', 'date_livraison', 'statut')
    search_fields = ('colis__reference',)
    list_filter = ('statut',)
    ordering = ('-date_envoi',)

admin.site.register(Destinataire)
class DestinataireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'telephone')
    search_fields = ('nom', 'email')
    list_filter = ('ville',)
    ordering = ('nom',)


class AgentAdmin(admin.ModelAdmin):
    list_display = ('utilisateur','nom_complet', 'email', 'telephone', 'zone_operation')
    search_fields = ('nom_complet', 'email')
    list_filter = ('zone_attribuee',)
    ordering = ('nom_complet',)
    def save_model(self, request, obj, form, change):
        if not obj.utilisateur:
            # Crée un CustomUser automatiquement si pas défini
            email = f"agent_{get_random_string(5)}@exemple.com"
            password = get_random_string(8)  # mot de passe aléatoire
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
              #  role="agent",  # si tu as un champ role
                is_active=True
            )
            user.groups.add(Group.objects.get_or_create(name='Agents')[0])
            obj.utilisateur = user
            # Optionnel : envoyer email à l'agent avec ses identifiants
            print(f"Agent créé : email={email}, motdepasse={password}")
        

            send_mail(
                subject="Vos identifiants Agent",
                message=f"Email: {email}\nMot de passe: {password}",
                accès ="medonjiojodeanas@gmail.com",
                from_email="no-reply@colisexpress.com",
                recipient_list=[email],
                fail_silently=False,
            )
        super().save_model(request, obj, form, change)

admin.site.register(Agent, AgentAdmin)

admin.site.register(Colis)
class ColisAdmin(admin.ModelAdmin):
    list_display = ('code_suivi','description', 'expediteur', 'destinataire', 'poids', 'statut')
    search_fields = ('code_suivi','description', 'expediteur', 'destinataire')
    list_filter = ('statut',)
    ordering = ('date_envoi',)

admin.site.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('destinataire', 'message', 'date_envoi', 'lu')
    search_fields = ('destinataire', 'message')
    list_filter = ('lu',)
    ordering = ('date_envoi',)



admin.site.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('titre', 'auteur', 'date_publication', 'statut')
    search_fields = ('titre', 'auteur')
    list_filter = ('statut', 'date_publication')
    ordering = ('date_publication',)

admin.site.register(EnregistrementScan)
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'user_type', 'telephone']
    list_filter = ['user_type']
    search_fields = ['username', 'email']

@admin.register(Transporteur)
class TransporteurAdmin(admin.ModelAdmin):
    list_display = ['user', 'entreprise', 'capacite', 'est_disponible']
    list_filter = ['est_disponible']
    search_fields = ['user__username', 'entreprise']
@admin.register(Tache)
class TacheAdmin(admin.ModelAdmin):
    list_display = ['colis', 'transporteur', 'agent', 'date_livraison_prevue', 'status']
    list_filter = ['status', 'date_attribution']
    search_fields = ['colis__reference']


from django.contrib import admin
from .models import DemandeInfos

@admin.register(DemandeInfos)
class DemandeInfosAdmin(admin.ModelAdmin):
    list_display = ("nom", "email", "telephone", "created_at")
    search_fields = ("nom", "email", "telephone", "adresse")
    readonly_fields = ("created_at",)
