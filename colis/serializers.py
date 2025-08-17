from rest_framework import serializers
from .models import Expediteur, Destinataire, Colis, Agent, EnregistrementScan,Utilisateur,Article,Notification,Livraison

class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id', 'username', 'email', 'telephone', 'adresse', 'role', 'date_creation']
        read_only_fields = ['date_creation']
class ExpediteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expediteur
        fields = ['id', 'nom', 'email', 'telephone', 'qr_code', 'date_creation','ville']

class DestinataireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destinataire
        fields = ['id', 'nom', 'email', 'telephone', 'qr_code', 'date_creation','ville']

class ColisSerializer(serializers.ModelSerializer):
    expediteur = ExpediteurSerializer(read_only=True)
    destinataire = DestinataireSerializer(read_only=True)

    class Meta:
        model = Colis
        fields = ['id', 'description', 'poids', 'adresse', 'statut', 'expediteur', 'destinataire', 'date_creation', 'date_envoi','code_suivi']

class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = ['user', 'nom_complet', 'email', 'zone_operation','zone_atribuee','telephone']
        read_only_fields = ['mot_de_passe']  # Ne pas exposer le mot de passe

class EnregistrementScanSerializer(serializers.ModelSerializer):
    colis = ColisSerializer(read_only=True)
    agent = AgentSerializer(read_only=True)

    class Meta:
        model = EnregistrementScan
        fields = ['id', 'colis', 'agent', 'qr_expediteur', 'qr_destinataire', 'type_scan', 'timestamp', 'resultat']

class NotificationSerializer(serializers.ModelSerializer):
    utilisateur = UtilisateurSerializer(read_only=True)
    class Meta:
        model = Notification
        fields = ['id', 'utilisateur', 'message', 'date', 'lu']
        read_only_fields = ['date']

class ArticleSerializer(serializers.ModelSerializer):
    auteur = UtilisateurSerializer(read_only=True)
    class Meta:
        model = Article
        fields = ['id', 'titre', 'contenu', 'auteur', 'date_publication']
        read_only_fields = ['date_publication']

class LivraisonSerializer(serializers.ModelSerializer):
    colis = ColisSerializer(read_only=True)
    class Meta:
        model = Livraison
        fields = ['id_livraison', 'code_suivi', 'date_livraison', 'date_envoi', 'colis', 'statut']
        read_only_fields = ['code_suivi', 'date_envoi']



from .models import DemandeInfos

class DemandeInfosSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeInfos
        fields = ["id", "nom", "email", "telephone", "adresse", "description_colis", "created_at"]
        read_only_fields = ["id", "created_at"]
