from django.shortcuts import render,redirect,get_object_or_404

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from functools import wraps
import requests


from .models import (CustomUser, Expediteur, Agent, Transporteur, Destinataire, Colis, Tache, Notification,Agent,DemandeInfos,EnregistrementScan, Notification,Article,
    Livraison,
)
from .serializers import (
    UserSerializer, ExpediteurSerializer, LoginSerializer, 
    InscriptionExpediteurSerializer, DestinataireSerializer, ColisSerializer,AgentSerializer,DemandeInfosSerializer,EnregistrementScanSerializer,NotificationSerializer,
    ArticleSerializer,LivraisonSerializer,TacheSerializer,UserSerializer
)

from .forms import InscriptionExpediteurForm, InscriptionAgentForm, ConnexionForm, DestinataireForm, ColisForm


# Décorateur personnalisé pour vérifier le type d'utilisateur
def user_type_required(user_type):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.user_type == user_type:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Accès non autorisé")
        return _wrapped_view
    return decorator


# ViewSet pour CRUD sur les modèles

class ColisViewSet(viewsets.ModelViewSet):
    serializer_class = ColisSerializer
    permission_classes = [IsAuthenticated]
    queryset = Colis.objects.all() 
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'expediteur':
            return Colis.objects.filter(expediteur__user=user)
        elif user.user_type == 'agent':
            return Colis.objects.filter(agent__user=user)
        elif user.user_type == 'transporteur':
            return Colis.objects.filter(transporteur__user=user)
        return Colis.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(expediteur=self.request.user.expediteur)
    
    @action(detail=True, methods=['post'])
    def attribuer_transporteur(self, request, pk=None):
        colis = self.get_object()
        transporteur_id = request.data.get('transporteur_id')
        date_livraison_prevue = request.data.get('date_livraison_prevue')
        
        try:
            transporteur = Transporteur.objects.get(id=transporteur_id)
            colis.transporteur = transporteur
            colis.date_livraison_prevue = date_livraison_prevue
            colis.statut = 'en_transit'
            colis.save()
            
            # Créer une tâche pour le transporteur
            Tache.objects.create(
                colis=colis,
                transporteur=transporteur,
                agent=colis.agent,
                date_livraison_prevue=date_livraison_prevue
            )
            
            # Créer une notification
            Notification.objects.create(
                destinataire=transporteur.user,
                type_notification='nouveau_colis',
                message=f"Nouveau colis {colis.reference} à livrer"
            )
            
            return Response({'status': 'Transporteur attribué'})
        except Transporteur.DoesNotExist:
            return Response({'error': 'Transporteur non trouvé'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def marquer_livre(self, request, pk=None):
        colis = self.get_object()
        colis.statut = 'livre'
        colis.date_livraison_reelle = timezone.now()
        colis.save()
        
        # Mettre à jour la tâche
        tache = Tache.objects.get(colis=colis)
        tache.est_terminee = True
        tache.save()
        
        # Envoyer une notification à l'expéditeur
        Notification.objects.create(
            destinataire=colis.expediteur.user,
            type_notification='livraison',
            message=f"Votre colis {colis.reference} a été livré avec succès"
        )
        
        return Response({'status': 'Colis marqué comme livré'})

# Autres ViewSets pour les modèles restants
class DestinataireViewSet(viewsets.ModelViewSet):
    queryset = Destinataire.objects.all()
    serializer_class = DestinataireSerializer
    permission_classes = [IsAuthenticated]

class ExpediteurViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Expediteur.objects.all()
    serializer_class = ExpediteurSerializer
    permission_classes = [IsAuthenticated]

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [permissions.IsAdminUser]


    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'expediteur':
            return Colis.objects.filter(expediteur__user=user)
        elif user.user_type == 'agent':
            return Colis.objects.filter(agent__user=user)
        elif user.user_type == 'transporteur':
            return Colis.objects.filter(transporteur__user=user)
        return Colis.objects.all()

    @action(detail=True, methods=['post'])
    def attribuer_transporteur(self, request, pk=None):
        colis = self.get_object()
        transporteur_id = request.data.get('transporteur_id')
        date_livraison_prevue = request.data.get('date_livraison_prevue')
        
        try:
            transporteur = Transporteur.objects.get(id=transporteur_id)
            colis.transporteur = transporteur
            colis.date_livraison_prevue = date_livraison_prevue
            colis.statut = 'en_transit'
            colis.save()
            
            # Créer une tâche pour le transporteur
            Tache.objects.create(
                colis=colis,
                transporteur=transporteur,
                agent=colis.agent,
                date_livraison_prevue=date_livraison_prevue
            )
            
            # Créer une notification
            Notification.objects.create(
                destinataire=transporteur.user,
                type_notification='nouveau_colis',
                message=f"Nouveau colis {colis.reference} à livrer"
            )
            
            return Response({'status': 'Transporteur attribué'})
        except Transporteur.DoesNotExist:
            return Response({'error': 'Transporteur non trouvé'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def marquer_livre(self, request, pk=None):
        colis = self.get_object()
        colis.statut = 'livre'
        colis.date_livraison_reelle = timezone.now()
        colis.save()
        
        # Mettre à jour la tâche
        tache = Tache.objects.get(colis=colis)
        tache.est_terminee = True
        tache.save()
        
        # Envoyer une notification à l'expéditeur
        Notification.objects.create(
            destinataire=colis.expediteur.user,
            type_notification='livraison',
            message=f"Votre colis {colis.reference} a été livré avec succès"
        )
        
        return Response({'status': 'Colis marqué comme livré'})


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
# --- Permissions basiques ---
class IsOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        u = request.user
        if isinstance(obj, Notification):
            return obj.utilisateur == u or u.is_staff
        if isinstance(obj, Colis):
            return obj.created_by == u or u.is_staff or obj.assigned_agent == u
        if isinstance(obj, Livraison):
            # livreur, créateur du colis, staff
            return (obj.livreur == u) or (obj.colis.created_by == u) or u.is_staff
        if isinstance(obj, DemandeInfos):
            return obj.auteur == u or u.is_staff
        return u.is_staff

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]

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
    

    def get_queryset(self):
        # un user voit ses notifications, staff voit tout
        if self.request.user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(utilisateur=self.request.user)

    @action(detail=False, methods=["get"], url_path="unread_count")
    def unread_count(self, request):
        count = self.get_queryset().filter(lu=False).count()
        return Response({"unread": count})

    @action(detail=True, methods=["post"], url_path="mark_read")
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.lu = True
        notif.save(update_fields=["lu"])
        return Response({"status": "ok"})

    @action(detail=False, methods=["post"], url_path="mark_all_read")
    def mark_all_read(self, request):
        qs = self.get_queryset().filter(lu=False)
        qs.update(lu=True)
        return Response({"status": "ok", "marked": qs.count()})



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

class TacheViewSet(viewsets.ModelViewSet):
    queryset = Tache.objects.all()
    serializer_class = TacheSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'transporteur':
            return Tache.objects.filter(transporteur__user=user)
        elif user.user_type == 'agent':
            return Tache.objects.filter(agent__user=user)
        return Tache.objects.all()

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def inscription(self, request):
        serializer = InscriptionExpediteurSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)




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



from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from .models import CustomUser, Expediteur, Agent, Transporteur, Destinataire, Colis
from .forms import InscriptionExpediteurForm, ConnexionForm, DestinataireForm, ColisForm
import requests

def index(request):
    return render(request, 'index.html')

def inscription(request):
    if request.method == 'POST':
        form = InscriptionExpediteurForm(request.POST)
        if form.is_valid():
            # Appel à l'API pour créer l'utilisateur
            data = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password1'],
                'telephone': form.cleaned_data['telephone'],
                'adresse': form.cleaned_data['adresse'],
                'user_type': 'expediteur'
            }
            
            try:
                response = requests.post('http://localhost:8000/api/auth/inscription_expediteur/', json=data)
                if response.status_code == 201:
                    user_data = response.json()
                    # Authentifier l'utilisateur
                    user = authenticate(
                        username=form.cleaned_data['username'],
                        password=form.cleaned_data['password1']
                    )
                    if user:
                        login(request, user)
                        messages.success(request, 'Votre compte a été créé avec succès!')
                        return redirect('creer_colis')
                else:
                    messages.error(request, 'Erreur lors de la création du compte')
            except requests.RequestException:
                messages.error(request, 'Erreur de connexion au serveur')
    else:
        form = InscriptionExpediteurForm()
    return render(request, 'inscription.html', {'form': form})

def connexion(request):
    if request.method == 'POST':
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Appel à l'API pour l'authentification
            data = {'username': username, 'password': password}
            try:
                response = requests.post('http://localhost:8000/api/auth/login/', json=data)
                if response.status_code == 200:
                    user_data = response.json()
                    user = authenticate(username=username, password=password)
                    if user:
                        login(request, user)
                        messages.success(request, f'Bienvenue {username}!')
                        
                        # Redirection en fonction du type d'utilisateur
                        if user.user_type == 'expediteur':
                            return redirect('dashboard_expediteur')
                        elif user.user_type == 'agent':
                            return redirect('dashboard_agent')
                        elif user.user_type == 'transporteur':
                            return redirect('dashboard_transporteur')
                        elif user.user_type == 'admin':
                            return redirect('admin:index')
                else:
                    messages.error(request, 'Identifiants invalides')
            except requests.RequestException:
                messages.error(request, 'Erreur de connexion au serveur')
    else:
        form = ConnexionForm()
    return render(request, 'connexion.html', {'form': form})


def deconnexion(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('index')
    # Vues pour expéditeurs
@login_required
@user_type_required('expediteur')
def dashboard_expediteur(request):
    expediteur = request.user.expediteur
    colis = Colis.objects.filter(expediteur=expediteur)
    
    context = {
        'colis': colis,
        'colis_count': colis.count(),
        'colis_livres_count': colis.filter(statut='livre').count(),
        'colis_transit_count': colis.filter(statut='en_transit').count(),
        'colis_probleme_count': colis.filter(statut='probleme').count(),
    }
    
    return render(request, 'dashboard_expediteur.html', context)

@login_required
@user_type_required('expediteur')


@login_required
def dashboard_expediteur(request):
    # Récupérer les colis de l'expéditeur via API
    try:
        response = requests.get(
            'http://localhost:8000/api/colis/',
            headers={'Authorization': f'Token {request.user.auth_token.key}'}
        )
        colis = response.json() if response.status_code == 200 else []
    except:
        colis = []
    
    return render(request, 'dashboard_expediteur.html', {'colis': colis})

@login_required
def creer_colis(request):
    if request.method == 'POST':
        destinataire_form = DestinataireForm(request.POST, prefix='destinataire')
        colis_form = ColisForm(request.POST, prefix='colis')
        
        if destinataire_form.is_valid() and colis_form.is_valid():
            # Créer le destinataire via API
            destinataire_data = {
                'nom_complet': destinataire_form.cleaned_data['nom_complet'],
                'telephone': destinataire_form.cleaned_data['telephone'],
                'adresse': destinataire_form.cleaned_data['adresse'],
                'ville': destinataire_form.cleaned_data['ville'],
                'code_postal': destinataire_form.cleaned_data['code_postal'],
            }
            
            try:
                # Créer le destinataire
                response = requests.post(
                    'http://localhost:8000/api/destinataires/',
                    json=destinataire_data,
                    headers={'Authorization': f'Token {request.user.auth_token.key}'}
                )
                
                if response.status_code == 201:
                    destinataire_id = response.json()['id']
                    
                    # Créer le colis
                    colis_data = {
                        'destinataire': destinataire_id,
                        'description': colis_form.cleaned_data['description'],
                        'poids': float(colis_form.cleaned_data['poids']),
                        'dimensions': colis_form.cleaned_data['dimensions'],
                        'valeur': float(colis_form.cleaned_data['valeur']) if colis_form.cleaned_data['valeur'] else None,
                    }
                    
                    response = requests.post(
                        'http://localhost:8000/api/colis/',
                        json=colis_data,
                        headers={'Authorization': f'Token {request.user.auth_token.key}'}
                    )
                    
                    if response.status_code == 201:
                        messages.success(request, 'Colis créé avec succès!')
                        return redirect('dashboard_expediteur')
                    else:
                        messages.error(request, 'Erreur lors de la création du colis')
                else:
                    messages.error(request, 'Erreur lors de la création du destinataire')
            except requests.RequestException:
                messages.error(request, 'Erreur de connexion au serveur')
    else:
        destinataire_form = DestinataireForm(prefix='destinataire')
        colis_form = ColisForm(prefix='colis')
    
    return render(request, 'creer_colis.html', {
        'destinataire_form': destinataire_form,
        'colis_form': colis_form
    })


@csrf_exempt
def creer_agent(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            # Récupération des données envoyées
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")
            telephone = data.get("telephone")
            adresse = data.get("adresse")

            if not username or not password:
                return JsonResponse({"error": "Username et password sont obligatoires"}, status=400)

            # Création de l'utilisateur
            user = User.objects.create_user(username=username, email=email, password=password)

            # Création de l'agent
            agent = Agent.objects.create(user=user, telephone=telephone, adresse=adresse)

            return JsonResponse({
                "message": "Agent créé avec succès",
                "agent": {
                    "id": agent.id,
                    "username": user.username,
                    "email": user.email,
                    "telephone": agent.telephone,
                    "adresse": agent.adresse,
                }
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

@login_required
@user_passes_test(lambda u: u.user_type == 'agent')
def dashboard_agent(request):
    # Récupérer les colis de l'agent via API
    try:
        response = requests.get(
            'http://localhost:8000/api/colis/',
            headers={'Authorization': f'Token {request.user.auth_token.key}'}
        )
        colis = response.json() if response.status_code == 200 else []
    except:
        colis = []
    
    # Récupérer les transporteurs disponibles
    try:
        response = requests.get(
            'http://localhost:8000/api/transporteurs/',
            headers={'Authorization': f'Token {request.user.auth_token.key}'}
        )
        transporteurs = response.json() if response.status_code == 200 else []
    except:
        transporteurs = []
    
    return render(request, 'dashboard_agent.html', {
        'colis': colis,
        'transporteurs': transporteurs
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'agent')
def attribuer_transporteur(request, colis_id):
    if request.method == 'POST':
        transporteur_id = request.POST.get('transporteur_id')
        date_livraison_prevue = request.POST.get('date_livraison_prevue')
        
        try:
            response = requests.post(
                f'http://localhost:8000/api/colis/{colis_id}/attribuer_transporteur/',
                json={
                    'transporteur_id': transporteur_id,
                    'date_livraison_prevue': date_livraison_prevue
                },
                headers={'Authorization': f'Token {request.user.auth_token.key}'}
            )
            
            if response.status_code == 200:
                messages.success(request, 'Transporteur attribué avec succès!')
            else:
                messages.error(request, 'Erreur lors de l\'attribution du transporteur')
        except requests.RequestException:
            messages.error(request, 'Erreur de connexion au serveur')
        
        return redirect('dashboard_agent')
    
    return redirect('dashboard_agent')

@login_required
@user_passes_test(lambda u: u.user_type == 'transporteur')
def dashboard_transporteur(request):
    # Récupérer les tâches du transporteur via API
    try:
        response = requests.get(
            'http://localhost:8000/api/taches/',
            headers={'Authorization': f'Token {request.user.auth_token.key}'}
        )
        taches = response.json() if response.status_code == 200 else []
    except:
        taches = []
    
    return render(request, 'dashboard_transporteur.html', {'taches': taches})

@login_required
@user_passes_test(lambda u: u.user_type == 'transporteur')
def marquer_livre(request, colis_id):
    try:
        response = requests.post(
            f'http://localhost:8000/api/colis/{colis_id}/marquer_livre/',
            headers={'Authorization': f'Token {request.user.auth_token.key}'}
        )
        
        if response.status_code == 200:
            messages.success(request, 'Colis marqué comme livré!')
        else:
            messages.error(request, 'Erreur lors de la mise à jour du colis')
    except requests.RequestException:
        messages.error(request, 'Erreur de connexion au serveur')
    
    return redirect('dashboard_transporteur')


@login_required
def api_colis_detail(request, pk):
    try:
        if request.user.user_type == 'expediteur':
            colis = Colis.objects.get(pk=pk, expediteur__user=request.user)
        elif request.user.user_type == 'agent':
            colis = Colis.objects.get(pk=pk, agent__user=request.user)
        elif request.user.user_type == 'transporteur':
            colis = Colis.objects.get(pk=pk, transporteur__user=request.user)
        else:
            colis = Colis.objects.get(pk=pk)
        
        data = {
            'reference': colis.reference,
            'expediteur': colis.expediteur.user.username,
            'destinataire': {
                'nom_complet': colis.destinataire.nom_complet,
                'telephone': colis.destinataire.telephone,
                'adresse': colis.destinataire.adresse,
                'ville': colis.destinataire.ville,
            },
            'description': colis.description,
            'poids': str(colis.poids),
            'statut': colis.get_statut_display(),
            'date_creation': colis.date_creation.strftime('%d/%m/%Y %H:%M'),
        }
        
        if colis.date_livraison_prevue:
            data['date_livraison_prevue'] = colis.date_livraison_prevue.strftime('%d/%m/%Y %H:%M')
        
        if colis.date_livraison_reelle:
            data['date_livraison_reelle'] = colis.date_livraison_reelle.strftime('%d/%m/%Y %H:%M')
        
        return JsonResponse(data)
    
    except Colis.DoesNotExist:
        return JsonResponse({'error': 'Colis non trouvé'}, status=404)


def api_colis_list(request):
    colis = Colis.objects.all().values("id", "expediteur__user__username", "destinataire__user__username", "description", "date_envoi")
    return JsonResponse(list(colis), safe=False)


def index(request):
    """Page d'accueil du site"""
    return render(request, 'index.html', {
        'title': 'Accueil - ColisExpress'
    })