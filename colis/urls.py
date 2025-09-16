from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import PasswordResetConfirmView
from .views import (
    InscriptionExpediteurAPIView,
    index, inscription, connexion, deconnexion,
    dashboard_expediteur, dashboard_agent, dashboard_transporteur,dashboard_admin,
    creer_colis, attribuer_transporteur, marquer_livre, creer_agent,
    api_colis_list, api_colis_detail,
    ExpediteurViewSet, DestinataireViewSet, ColisViewSet,
    AgentViewSet, EnregistrementScanViewSet, ScanAPIView, ArticleViewSet,
    NotificationViewSet, LivraisonViewSet, DemandeInfosViewSet, TacheViewSet,
    AuthViewSet,contact_view, LoginAPIView,tache_form,TransporteurViewSet,CustomLoginView
)

# ===================== ROUTER API =====================
router = DefaultRouter()
router.register(r'expediteurs', ExpediteurViewSet)
router.register(r'destinataires', DestinataireViewSet)
router.register(r'colis', ColisViewSet)
router.register(r'agents', AgentViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'articles', ArticleViewSet)
router.register(r'livraisons', LivraisonViewSet)
router.register(r'scans', EnregistrementScanViewSet)
router.register(r'demandes', DemandeInfosViewSet, basename='demandes')
router.register(r'taches', TacheViewSet, basename='taches')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'transporteurs', TransporteurViewSet)

# ===================== Swagger =====================
schema_view = get_schema_view(
    openapi.Info(
        title="Gestion Colis API",
        default_version='v1',
        description="Documentation de l'API Gestion Colis",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# ===================== URLS =====================
urlpatterns = [
    # ---------------- HTML ----------------
    path('', index, name='index'),
    path('inscription/', inscription, name='inscription'),
    path('connexion/', connexion, name='connexion'),
    path('deconnexion/', deconnexion, name='deconnexion'),
    path('tache/', tache_form, name='tache_form'), 
    
    # Dashboards
    path('dashboard/expediteur/', dashboard_expediteur, name='dashboard_expediteur'),
    path('dashboard/agent/', dashboard_agent, name='dashboard_agent'),
    path('dashboard/transporteur/', dashboard_transporteur, name='dashboard_transporteur'),
    path('dashboard/', dashboard_admin, name='dashboard_admin'),
    path('inscrire-agent/', views.inscrire_agent, name='inscrire_agent'),
    path('connexion1/', CustomLoginView.as_view(), name='connexion1'),
    # Gestion des colis
    path('colis/creer/', creer_colis, name='creer_colis'),
    re_path(r'^colis/(?P<colis_id>[0-9a-f-]+)/attribuer-transporteur/$', attribuer_transporteur, name='attribuer_transporteur'),
    # Ajoute autres URLs si nécessaire
    path('colis/<int:colis_id>/marquer-livre/', marquer_livre, name='marquer_livre'),
    path("colis/<uuid:pk>/details/", views.details_colis, name="details_colis"),
    path("colis/<uuid:pk>/supprimer/", views.supprimer_colis, name="supprimer_colis"),
    # Administration
    path('admin/creer-agent/', creer_agent, name='creer_agent'),

    # ---------------- API ----------------
    path('api/', include(router.urls)),  # Toutes les ViewSets
    path('api/auth/inscription/', InscriptionExpediteurAPIView.as_view(), name='inscription_expediteur'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/colis/', api_colis_list, name='api_colis_list'),
    path('api/colis/<int:pk>/', api_colis_detail, name='api_colis_detail'),
    path('api/scan/', ScanAPIView.as_view(), name='api_scan'),
    path("api/login/", LoginAPIView.as_view(), name="api_login"),
    path("creer-agent/", views.creer_agent, name="creer_agent"),
    path("login/", auth_views.LoginView.as_view(template_name="connexion.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # ---------------- Swagger ----------------
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path("contact/", contact_view, name="contact"),

    # ---------------- CRUD-AGENT ----------------
    path("agents/", views.liste_agents, name="liste_agents"),
    path("agents/creer/", views.creer_agent, name="creer_agent"),
    path("agents/modifier/<int:pk>/", views.modifier_agent, name="modifier_agent"),
    path("agents/supprimer/<int:pk>/", views.supprimer_agent, name="supprimer_agent"),
     # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),


]
