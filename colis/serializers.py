from rest_framework import serializers
from .models import Expediteur, Destinataire, Colis, Agent, EnregistrementScan,Article,Notification,Livraison, Transporteur,Tache,CustomUser

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'telephone', 'adresse','password', ]
        read_only_fields = ['date_creation']
    def create(self, validated_data):
        password = validated_data.pop('password')   # ✅ on enlève le password des data
        utilisateur = CustomUser(**validated_data)
        utilisateur.set_password(password)          # ✅ hashage ici
        utilisateur.save()
        return utilisateur
class ExpediteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expediteur
        fields = ['id', 'nom', 'email', 'telephone', 'qr_code', 'date_creation','ville']

class DestinataireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destinataire
        fields = ['id', 'nom_complet', 'email', 'telephone', 'qr_code', 'date_creation','ville']


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = ['user', 'nom_complet', 'email', 'zone_operation','zone_atribuee','telephone','mot_de_passe']
        read_only_fields = ['mot_de_passe']  # Ne pas exposer le mot de passe


class TransporteurSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = Transporteur
        fields = '__all__'

class ColisSerializer(serializers.ModelSerializer):
    expediteur = ExpediteurSerializer(read_only=True)
    destinataire = DestinataireSerializer(read_only=True)
    expediteur_id = serializers.PrimaryKeyRelatedField(
        queryset=Expediteur.objects.all(), source='expediteur', write_only=True
    )
    destinataire_id = serializers.PrimaryKeyRelatedField(
        queryset=Destinataire.objects.all(), source='destinataire', write_only=True
    )
    agent = AgentSerializer(read_only=True)
    transporteur = TransporteurSerializer(read_only=True)
    class Meta:
        model = Colis
        fields = ['id', 'description', 'poids', 'adresse', 'STATUT_CHOICES', 'transporteur','expediteur','agent', 'destinataire', 'date_creation', 'date_envoi','code_suivi','expediteur_id','destinataire_id']


class EnregistrementScanSerializer(serializers.ModelSerializer):
    colis = ColisSerializer(read_only=True)
    agent = AgentSerializer(read_only=True)
    id_colis = serializers.PrimaryKeyRelatedField(
        queryset=Colis.objects.all(), source='colis', write_only=True
    )
    id_agent= serializers.PrimaryKeyRelatedField(
        queryset=Agent.objects.all(), source='agent', write_only=True
    )
    class Meta:
        model = EnregistrementScan
        fields = ['id', 'colis', 'agent', 'qr_expediteur', 'qr_destinataire', 'type_scan', 'timestamp', 'resultat','id_colis','id_agent']

class NotificationSerializer(serializers.ModelSerializer):
    utilisateur = UserSerializer(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), source='utilisateur', write_only=True
    )
    class Meta:
        model = Notification
        fields = ['id', 'utilisateur', 'message', 'date', 'lu', 'canal','meta']
        read_only_fields = ['date']

class ArticleSerializer(serializers.ModelSerializer):
    auteur = UserSerializer(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), source='auteur', write_only=True
    )
    class Meta:
        model = Article
        fields = ['id', 'titre', 'contenu', 'auteur', 'date_publication']
        read_only_fields = ['date_publication']

class LivraisonSerializer(serializers.ModelSerializer):
    colis = ColisSerializer(read_only=True)
    id_livraison = serializers.PrimaryKeyRelatedField(
        queryset=Colis.objects.all(), source='colis', write_only=True
    )
    class Meta:
        model = Livraison
        fields = ['id_livraison', 'code_suivi', 'date_livraison', 'date_envoi', 'colis', 'statut']
        read_only_fields = ['code_suivi', 'date_envoi']



from .models import DemandeInfos

class DemandeInfosSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeInfos
        fields = ["id", "nom", "email", "telephone", "adresse", "description_colis", "created_at","reponse","repondu","auteur"]
        read_only_fields = ["id", "created_at"]


class TacheSerializer(serializers.ModelSerializer):
    colis = ColisSerializer(read_only=True)
    transporteur = TransporteurSerializer(read_only=True)
    agent = AgentSerializer(read_only=True)
    
    class Meta:
        model = Tache
        fields = '__all__'


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError("Compte désactivé.")
            else:
                raise serializers.ValidationError("Identifiants invalides.")
        else:
            raise serializers.ValidationError("Must include username and password.")

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
        # Extraire les champs spécifiques
        password_confirm = validated_data.pop('password_confirm')
        entreprise = validated_data.pop('entreprise', '')
        telephone = validated_data.pop('telephone')
        adresse = validated_data.pop('adresse')
        
        # Créer l'utilisateur
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            user_type='expediteur',
            telephone=telephone,
            adresse=adresse
        )
        
        # Créer le profil expéditeur
        Expediteur.objects.create(user=user, entreprise=entreprise)
        
        return user
