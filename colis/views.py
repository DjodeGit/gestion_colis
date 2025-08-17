from django.shortcuts import render

# Create your views here.
from rest_framework.permissions import IsAuthenticated 
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Expediteur, Destinataire, Colis, Agent, EnregistrementScan,Notification,Livraison,Article,Utilisateur
from .serializers import (
    ExpediteurSerializer, DestinataireSerializer, ColisSerializer,
    AgentSerializer, EnregistrementScanSerializer,NotificationSerializer,
    LivraisonSerializer,ArticleSerializer,UtilisateurSerializer
)

# ViewSet pour CRUD sur les modèles
class UtilisateurViewSet(viewsets.ModelViewSet):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Créer un utilisateur et hacher le mot de passe
        utilisateur = serializer.save()
        utilisateur.set_password(serializer.validated_data['password'])
        utilisateur.save()
        # Notifier l'utilisateur de la création de son compte
        Notification.objects.create(
            utilisateur=utilisateur,
            message=f"Bienvenue, {utilisateur.username}! Votre compte a été créé."
        )

class ExpediteurViewSet(viewsets.ModelViewSet):
    queryset = Expediteur.objects.all()
    serializer_class = ExpediteurSerializer
    permission_classes = [permissions.IsAuthenticated]


class DestinataireViewSet(viewsets.ModelViewSet):
    queryset = Destinataire.objects.all()
    serializer_class = DestinataireSerializer
    permission_classes = [permissions.IsAuthenticated]


class ColisViewSet(viewsets.ModelViewSet):
    queryset = Colis.objects.all()
    serializer_class = ColisSerializer
    permission_classes = [permissions.IsAuthenticated]

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [permissions.IsAuthenticated]


class EnregistrementScanViewSet(viewsets.ModelViewSet):
    queryset = EnregistrementScan.objects.all()
    serializer_class = EnregistrementScanSerializer
    permission_classes = [permissions.IsAuthenticated]



# API spécifique pour le scan
class ScanAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        qr_expediteur = request.data.get('qr_expediteur')
        qr_destinataire = request.data.get('qr_destinataire')
        agent_id = request.data.get('agent_id')
        type_scan = request.data.get('type_scan')

        try:
            colis = Colis.objects.get(
                expediteur__qr_code=qr_expediteur,
                destinataire__qr_code=qr_destinataire
            )
            agent = Agent.objects.get(id=agent_id)
            scan = EnregistrementScan.objects.create(
                colis=colis,
                agent=agent,
                qr_expediteur=qr_expediteur,
                qr_destinataire=qr_destinataire,
                type_scan=type_scan,
                resultat='Succès'
            )
            # Créer une notification pour l'expéditeur et le destinataire
            Notification.objects.create(
                utilisateur=colis.expediteur.utilisateur,
                message=f"Votre colis {colis.id} a été scanné pour {type_scan}."
            )
            Notification.objects.create(
                utilisateur=colis.destinataire.utilisateur,
                message=f"Votre colis {colis.id} a été scanné pour {type_scan}."
            )
            # Si c'est un scan de livraison, créer/mettre à jour une Livraison
            if type_scan == 'livraison':
                livraison, created = Livraison.objects.get_or_create(
                    colis=colis,
                    defaults={'statut': 'livre', 'date_livraison': timezone.now()}
                )
                if not created:
                    livraison.statut = 'livre'
                    livraison.date_livraison = timezone.now()
                    livraison.save()
                # Mettre à jour le statut du colis
                colis.statut = 'livre'
                colis.date_expedition = colis.date_expedition or timezone.now()
                colis.save()
            serializer = EnregistrementScanSerializer(scan)
            return Response(
                {'message': 'Scan enregistré', 'scan': serializer.data},
                status=status.HTTP_201_CREATED
            )
        except Colis.DoesNotExist:
            return Response(
                {'error': 'Colis non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Agent.DoesNotExist:
            return Response(
                {'error': 'Agent non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Restreindre les notifications à celles de l'utilisateur connecté
        return Notification.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save()
        # Optionnel : ajouter une logique pour envoyer un email ou une notification push

    def perform_update(self, serializer):
        notification = serializer.save()
        # Marquer comme lu si le champ 'lu' est mis à jour
        if notification.lu:
            Notification.objects.filter(id=notification.id).update(lu=True)

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Attribuer l'utilisateur connecté comme auteur
        serializer.save(auteur=self.request.user)
        # Notifier tous les agents
        agents = Agent.objects.all()
        for agent in agents:
            Notification.objects.create(
                utilisateur=agent.utilisateur,
                message=f"Nouvel article publié : {serializer.validated_data['titre']}."
            )

class LivraisonViewSet(viewsets.ModelViewSet):
    queryset = Livraison.objects.all()
    serializer_class = LivraisonSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        livraison = serializer.save()
        # Créer une notification pour l'expéditeur et le destinataire
        colis = livraison.colis
        Notification.objects.create(
            utilisateur=colis.expediteur.utilisateur,
            message=f"Votre colis {colis.id} est en cours de livraison (code: {livraison.code_suivi})."
        )
        Notification.objects.create(
            utilisateur=colis.destinataire.utilisateur,
            message=f"Votre colis {colis.id} est en cours de livraison (code: {livraison.code_suivi})."
        )

    def perform_update(self, serializer):
        livraison = serializer.save()
        # Si le statut passe à 'livre', mettre à jour la date de livraison et notifier
        if livraison.statut == 'livre':
            livraison.date_livraison = timezone.now()
            livraison.save()
            Notification.objects.create(
                utilisateur=livraison.colis.destinataire.utilisateur,
                message=f"Votre colis {livraison.colis.id} a été livré (code: {livraison.code_suivi})."
            )



from rest_framework import viewsets, permissions
from .models import DemandeInfos
from .serializers import DemandeInfosSerializer

class DemandeInfosViewSet(viewsets.ModelViewSet):
    """
    - POST (create) : public (client)
    - list/retrieve/update/destroy : réservé au staff via IsAdminUser
    """
    queryset = DemandeInfos.objects.all()
    serializer_class = DemandeInfosSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

# colis/views.py
from django.shortcuts import render

def demande_page(request):
    """Page HTML qui contient le formulaire JS POST vers /api/demandes/"""
    return render(request, "colis.demande_api.html")


