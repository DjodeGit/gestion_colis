from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Expediteur,Destinataire,Colis,Notification,Article,Agent,Livraison,EnregistrementScan,Utilisateur
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

admin.site.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'email', 'telephone', 'zone_operation')
    search_fields = ('nom', 'email')
    list_filter = ('zone_attribuee',)
    ordering = ('nom',)

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
admin.site.register(Utilisateur)


from django.contrib import admin
from .models import DemandeInfos

@admin.register(DemandeInfos)
class DemandeInfosAdmin(admin.ModelAdmin):
    list_display = ("nom", "email", "telephone", "created_at")
    search_fields = ("nom", "email", "telephone", "adresse")
    readonly_fields = ("created_at",)
