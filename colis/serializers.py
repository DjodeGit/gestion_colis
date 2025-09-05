from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import (
    Expediteur, Destinataire, Colis, Agent, EnregistrementScan,
    Article, Notification, Livraison, Transporteur, Tache, CustomUser, DemandeInfos
)

# ---------------- UTILISATEURS ----------------
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'telephone', 'adresse', 'password', 'user_type']
        read_only_fields = ['id', 'date_creation']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

# ---------------- EXPEDITEUR ----------------
class ExpediteurSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), source="user", write_only=True)

    class Meta:
        model = Expediteur
        fields = ['id', 'user', 'user_id', 'nom', 'email', 'telephone', 'ville', 'entreprise', 'qr_code', 'date_creation']

# ---------------- DESTINATAIRE ----------------
class DestinataireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destinataire
        fields = ['id', 'nom_complet', 'email', 'telephone', 'ville', 'qr_code', 'date_creation']

# ---------------- AGENT ----------------
class AgentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), source="user", write_only=True)

    class Meta:
        model = Agent
        fields = ['id', 'user', 'user_id', 'nom_complet', 'email', 'telephone', 'zone_operation', 'zone_attribuee']
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(
            username=user_data['email'],
            email=user_data['email'],
            password=user_data['password']
        )
        user.groups.add(Group.objects.get_or_create(name='Agents')[0])
        agent = Agent.objects.create(user=user, **validated_data)
        return agent

# ---------------- TRANSPORTEUR ----------------
class TransporteurSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), source="user", write_only=True)

    class Meta:
        model = Transporteur
        fields = ['id', 'user', 'user_id', 'nom', 'telephone', 'vehicule', 'matricule', 'email']

# ---------------- COLIS ----------------
class ColisSerializer(serializers.ModelSerializer):
    expediteur = ExpediteurSerializer(read_only=True)
    expediteur_id = serializers.PrimaryKeyRelatedField(queryset=Expediteur.objects.all(), source='expediteur', write_only=True)
    destinataire = DestinataireSerializer(read_only=True)
    destinataire_id = serializers.PrimaryKeyRelatedField(queryset=Destinataire.objects.all(), source='destinataire', write_only=True)
    agent = AgentSerializer(read_only=True)
    transporteur = TransporteurSerializer(read_only=True)
    
    class Meta:
        model = Colis
        fields = ['id', 'description', 'poids', 'adresse', 'statut', 'code_suivi',
                  'expediteur', 'expediteur_id', 'destinataire', 'destinataire_id',
                  'agent', 'transporteur', 'date_creation', 'date_envoi']
        read_only_fields = ["utilisateur"] 
        
    def create(self, validated_data):
        validated_data["utilisateur"] = self.context["request"].user  # ✅ utilisateur auto
        return super().create(validated_data)
# ---------------- SCAN ----------------
class EnregistrementScanSerializer(serializers.ModelSerializer):
    colis = ColisSerializer(read_only=True)
    colis_id = serializers.PrimaryKeyRelatedField(queryset=Colis.objects.all(), source='colis', write_only=True)
    agent = AgentSerializer(read_only=True)
    agent_id = serializers.PrimaryKeyRelatedField(queryset=Agent.objects.all(), source='agent', write_only=True)

    class Meta:
        model = EnregistrementScan
        fields = ['id', 'colis', 'colis_id', 'agent', 'agent_id', 'qr_expediteur', 'qr_destinataire', 'type_scan', 'timestamp', 'resultat']

# ---------------- NOTIFICATIONS ----------------
class NotificationSerializer(serializers.ModelSerializer):
    utilisateur = UserSerializer(read_only=True)
    utilisateur_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), source='utilisateur', write_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'utilisateur', 'utilisateur_id', 'message', 'date', 'lu', 'canal', 'meta']
        read_only_fields = ['date']

# ---------------- ARTICLES ----------------
class ArticleSerializer(serializers.ModelSerializer):
    auteur = UserSerializer(read_only=True)
    auteur_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), source='auteur', write_only=True)

    class Meta:
        model = Article
        fields = ['id', 'titre', 'contenu', 'auteur', 'auteur_id', 'date_publication']
        read_only_fields = ['date_publication']

# ---------------- LIVRAISON ----------------
class LivraisonSerializer(serializers.ModelSerializer):
    colis = ColisSerializer(read_only=True)
    colis_id = serializers.PrimaryKeyRelatedField(queryset=Colis.objects.all(), source='colis', write_only=True)

    class Meta:
        model = Livraison
        fields = ['colis', 'colis_id', 'code_suivi', 'date_envoi', 'date_livraison', 'statut']
        read_only_fields = ['code_suivi', 'date_envoi']

# ---------------- DEMANDE INFOS ----------------
class DemandeInfosSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeInfos
        fields = ["id", "nom", "email", "telephone", "adresse", "description_colis", "created_at", "reponse", "repondu", "auteur"]
        read_only_fields = ["id", "created_at"]

# ---------------- TACHE ----------------
class TacheSerializer(serializers.ModelSerializer):
    colis = ColisSerializer(read_only=True)
    transporteur = TransporteurSerializer(read_only=True)
    agent = AgentSerializer(read_only=True)

    class Meta:
        model = Tache
        fields = '__all__'

# ---------------- AUTH ----------------
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError(_("Identifiants incorrects"), code="authorization")
        else:
            raise serializers.ValidationError(_("Email et mot de passe requis"), code="authorization")

        data["user"] = user
        return data
class InscriptionExpediteurSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    telephone = serializers.CharField(required=True)
    adresse = serializers.CharField(required=True)
    entreprise = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password_confirm', 'telephone', 'adresse', 'entreprise']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        entreprise = validated_data.pop('entreprise', '')
        telephone = validated_data.pop('telephone')
        adresse = validated_data.pop('adresse')

        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            user_type='expediteur',
            telephone=telephone,
            adresse=adresse
        )
        Expediteur.objects.create(user=user, entreprise=entreprise)
        return user
