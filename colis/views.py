from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from functools import wraps
from django.core.mail import send_mail   # <<< AJOUTER CETTE LIGNE
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated,IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes

from .models import (
    CustomUser, Expediteur, Agent, Transporteur, Destinataire, Colis,
    Tache, Notification, DemandeInfos, EnregistrementScan, Article, Livraison
)
from django.core.mail import send_mail   # <<< AJOUTER CETTE LIGNE
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .serializers import (
    UserSerializer, ExpediteurSerializer, LoginSerializer,
    InscriptionExpediteurSerializer, DestinataireSerializer, ColisSerializer,
    AgentSerializer, DemandeInfosSerializer, EnregistrementScanSerializer,
    NotificationSerializer, ArticleSerializer, LivraisonSerializer, TacheSerializer,TransporteurSerializer
)
from .forms import (
    InscriptionExpediteurForm, ConnexionForm, DestinataireForm, ColisForm,ContactForm
)

# =====================================
# Décorateur personnalisé pour le type d'utilisateur
# =====================================
def user_type_required(user_type):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.user_type == user_type:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Accès non autorisé")
        return _wrapped_view
    return decorator

# =====================================
# ViewSets DRF (API CRUD)
# =====================================

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
        return Colis.objects.all()

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


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

            Tache.objects.create(
                colis=colis,
                transporteur=transporteur,
                agent=colis.agent,
                date_livraison_prevue=date_livraison_prevue
            )
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

        tache = Tache.objects.filter(colis=colis).first()
        if tache:
            tache.est_terminee = True
            tache.save()

        Notification.objects.create(
            destinataire=colis.expediteur.user,
            type_notification='livraison',
            message=f"Votre colis {colis.reference} a été livré avec succès"
        )
        return Response({'status': 'Colis marqué comme livré'})

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
    permission_classes = [IsAdminUser]

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(destinataire=self.request.user)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(lu=False).count()
        return Response({"unread": count})

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.lu = True
        notif.save(update_fields=["lu"])
        return Response({"status": "ok"})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        qs = self.get_queryset().filter(lu=False)
        qs.update(lu=True)
        return Response({"status": "ok", "marked": qs.count()})

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(auteur=self.request.user)
        for agent in Agent.objects.all():
            Notification.objects.create(
                destinataire=agent.user,
                message=f"Nouvel article publié : {serializer.validated_data['titre']}."
            )

class LivraisonViewSet(viewsets.ModelViewSet):
    queryset = Livraison.objects.all()
    serializer_class = LivraisonSerializer
    permission_classes = [IsAuthenticated]

class TacheViewSet(viewsets.ModelViewSet):
    queryset = Tache.objects.all()
    serializer_class = TacheSerializer
    permission_classes = [IsAuthenticated]
    def perform_create(self, serializer):
        # Assigne l'agent connecté
        serializer.save(agent=self.request.user.agent)

class EnregistrementScanViewSet(viewsets.ModelViewSet):
    queryset = EnregistrementScan.objects.all()
    serializer_class = EnregistrementScanSerializer
    permission_classes = [IsAuthenticated]

# =====================================
# API spécifiques
# =====================================

class ScanAPIView(APIView):
    permission_classes = [IsAuthenticated]

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
            # Notification
            Notification.objects.create(
                destinataire=colis.expediteur.user,
                message=f"Votre colis {colis.reference} a été scanné ({type_scan})."
            )
            Notification.objects.create(
                destinataire=colis.destinataire.user,
                message=f"Votre colis {colis.reference} a été scanné ({type_scan})."
            )
            return Response({'message': 'Scan enregistré', 'scan_id': scan.id}, status=status.HTTP_201_CREATED)

        except Colis.DoesNotExist:
            return Response({'error': 'Colis non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        except Agent.DoesNotExist:
            return Response({'error': 'Agent non trouvé'}, status=status.HTTP_404_NOT_FOUND)

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        })

    @action(detail=False, methods=['post'])
    def inscription(self, request):
        serializer = InscriptionExpediteurSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }, status=status.HTTP_201_CREATED)

class DemandeInfosViewSet(viewsets.ModelViewSet):
    queryset = DemandeInfos.objects.all()
    serializer_class = DemandeInfosSerializer
    permission_classes = [IsAuthenticated]


class InscriptionExpediteurAPIView(APIView):
    def post(self, request, format=None):
        form = InscriptionExpediteurForm(request.data)
        if form.is_valid():
            form.save()
            return Response({"message": "Expéditeur inscrit avec succès"}, status=status.HTTP_201_CREATED)
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        # Déterminer le rôle
        role = None
        if hasattr(user, "agent"):
            role = "agent"
        elif hasattr(user, "expediteur"):
            role = "expediteur"
        elif hasattr(user, "expediteur"):
            role = "transporteur"
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "role": role
        })

class TransporteurViewSet(viewsets.ModelViewSet):
    queryset = Transporteur.objects.all()
    serializer_class = TransporteurSerializer
    permission_classes = [IsAdminUser]

# =====================================
# Vues HTML (Pages & Dashboards)
# =====================================

def index(request):
    return render(request, 'index.html')

# Vue pour le formulaire
def tache_form(request):
    return render(request, 'creer_tache.html')

def inscription(request):
    form = InscriptionExpediteurForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('dashboard_expediteur')
    return render(request, 'inscription.html', {'form': form})

def connexion(request):
    form = ConnexionForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        if user.user_type == 'expediteur':
            return redirect('dashboard_expediteur')
        elif user.user_type == 'agent':
            return redirect('dashboard_agent')
        elif user.user_type == 'transporteur':
            return redirect('dashboard_transporteur')
    return render(request, 'connexion.html', {'form': form})

@login_required
def deconnexion(request):
    logout(request)
    return redirect('index')

@login_required
@user_type_required('expediteur')
def dashboard_expediteur(request):
    colis = Colis.objects.filter(expediteur=request.user.expediteur)
    context = {
        'colis': colis,
        'colis_count': colis.count(),
        'colis_livres_count': colis.filter(statut='livre').count(),
        'colis_transit_count': colis.filter(statut='en_transit').count(),
        'colis_probleme_count': colis.filter(statut='probleme').count(),
    }
    return render(request, 'dashboard_expediteur.html', context)

@login_required
@user_type_required('agent')
def dashboard_agent(request):
    colis = Colis.objects.filter(agent=request.user.agent)
    transporteurs = Transporteur.objects.all()
    return render(request, 'dashboard_agent.html', {'colis': colis, 'transporteurs': transporteurs})

@login_required
@user_type_required('transporteur')
def dashboard_transporteur(request):
    taches = Tache.objects.filter(transporteur__user=request.user)
    return render(request, 'dashboard_transporteur.html', {'taches': taches})

@login_required
@user_type_required('expediteur')
def creer_colis(request):
    colis_form = ColisForm(request.POST or None, prefix='colis')
    destinataire_form = DestinataireForm(request.POST or None, prefix='destinataire')

    if request.method == 'POST' and colis_form.is_valid() and destinataire_form.is_valid():
        destinataire = destinataire_form.save()
        colis = colis_form.save(commit=False)
        colis.destinataire = destinataire
        colis.expediteur = request.user.expediteur
        colis.utilisateur = request.user
        colis.save()
        return redirect('dashboard_expediteur')

    return render(request, 'creer_colis.html', {'colis_form': colis_form, 'destinataire_form': destinataire_form})

@login_required
@user_type_required('agent')
def attribuer_transporteur(request, colis_id):
    if request.method == 'POST':
        colis = get_object_or_404(Colis, id=colis_id)
        transporteur_id = request.POST.get('transporteur_id')
        transporteur = get_object_or_404(Transporteur, id=transporteur_id)
        colis.transporteur = transporteur
        colis.statut = 'en_transit'
        colis.save()
    return redirect('dashboard_agent')

@login_required
@user_type_required('transporteur')
def marquer_livre(request, colis_id):
    colis = get_object_or_404(Colis, id=colis_id)
    colis.statut = 'livre'
    colis.date_livraison_reelle = timezone.now()
    colis.save()
    tache = Tache.objects.filter(colis=colis).first()
    if tache:
        tache.est_terminee = True
        tache.save()
    return redirect('dashboard_transporteur')

@login_required
@user_type_required('agent')
def creer_agent(request):
    if request.method == 'POST':
        # Formulaire admin pour créer agent
        pass
    return render(request, 'creer_agent.html')

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def api_colis_list(request):
    if request.method == 'GET':
        colis = Colis.objects.all()
        serializer = ColisSerializer(colis, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ColisSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def api_colis_detail(request, pk):
    try:
        colis = Colis.objects.get(pk=pk)
    except Colis.DoesNotExist:
        return Response({'error': 'Colis non trouvé'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ColisSerializer(colis)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ColisSerializer(colis, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        colis.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]

            # Message formaté
            full_message = f"Message de : {name} ({email})\n\n{message}"

            # Envoi de l'email
            send_mail(
                subject,                      # Sujet
                full_message,                 # Contenu
                settings.DEFAULT_FROM_EMAIL,  # Expéditeur
                ["medonjiojodeanas@gmail.com"],     # Destinataire (toi)
            )

            messages.success(request, "Votre message a été envoyé avec succès ✅")
            return redirect("contact")
    else:
        form = ContactForm()

    return render(request, "index.html", {"form": form})

@login_required
def details_colis(request, pk):
    colis = get_object_or_404(Colis, pk=pk)
    return render(request, "details_colis.html", {"colis": colis})

@login_required
def supprimer_colis(request, pk):
    colis = get_object_or_404(Colis, pk=pk)
    if request.method == "POST":  # On supprime seulement si c'est une requête POST
        colis.delete()
        return redirect("dashboard_expediteur")  # Redirige vers le dashboard après suppression
    return render(request, "supprimer_colis.html", {"colis": colis})


from django.contrib.auth.views import LoginView
from .forms import EmailAuthenticationForm

class EmailLoginView(LoginView):
    template_name = "connexion.html"
    authentication_form = EmailAuthenticationForm

    def get_success_url(self):
        # Redirection selon le rôle
        user = self.request.user
        if hasattr(user, "agent"):
            return "/dashboard/agent/"
        elif hasattr(user, "expediteur"):
            return "/dashboard/expediteur/"
        elif hasattr(user, "transporteur"):
            return "/dashboard/transporteur/"
        return "/"

# views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from .models import Agent
from .forms import AgentCreationForm, AgentUpdateForm

def is_admin(user):
    return user.is_superuser  # Seul l’administrateur

@login_required
@user_passes_test(is_admin)
def creer_agent(request):
    if request.method == "POST":
        form = AgentCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("liste_agents")
    else:
        form = AgentCreationForm()
    return render(request, "dashboard/creer_agent.html", {"form": form})

@login_required
@user_passes_test(is_admin)
def liste_agents(request):
    agents = Agent.objects.all()
    return render(request, "dashboard/liste_agents.html", {"agents": agents})

@login_required
@user_passes_test(is_admin)
def modifier_agent(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    if request.method == "POST":
        form = AgentUpdateForm(request.POST, instance=agent)
        if form.is_valid():
            form.save()
            return redirect("liste_agents")
    else:
        form = AgentUpdateForm(instance=agent)
    return render(request, "dashboard/modifier_agent.html", {"form": form})

@login_required
@user_passes_test(is_admin)
def supprimer_agent(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    if request.method == "POST":
        agent.user.delete()  # Supprime aussi le compte utilisateur
        agent.delete()
        return redirect("liste_agents")
    return render(request, "dashboard/supprimer_agent.html", {"agent": agent})
