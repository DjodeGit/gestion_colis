from django.urls import path
from . import views
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    ExpediteurViewSet, DestinataireViewSet, ColisViewSet,
    AgentViewSet, EnregistrementScanViewSet, ScanAPIView,ArticleViewSet,
    NotificationViewSet,LivraisonViewSet,DemandeInfosViewSet,TacheViewSet
)

# Créer un routeur pour les ViewSets
router = DefaultRouter()
# router.register(r'expediteurs', ExpediteurViewSet)
# router.register(r'destinataires', DestinataireViewSet)
# router.register(r'taches', TacheViewSet,basename='tache')
# router.register(r'colis', ColisViewSet)
# router.register(r'agents', AgentViewSet)
# router.register(r'notifications', NotificationViewSet)
# router.register(r'articles', ArticleViewSet)
# router.register(r'livraisons', LivraisonViewSet)
# router.register(r'scans', EnregistrementScanViewSet)
# router.register(r'demandes', DemandeInfosViewSet, basename='demandes')
#router.register(r'auth', AuthViewSet, basename='auth')


schema_view = get_schema_view(
    openapi.Info(
        title="API Colis - Demandes",
        default_version='v1',
        description="API pour soumettre des demandes d'informations (clients) et pour que l'entreprise les consulte.",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('', include(router.urls)),
    # docs swagger (optionnel, utile en dev)
    re_path(r'^docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]






from django.urls import path
from . import views

urlpatterns = [
    # Pages principales
    path('', views.index, name='index'),
    
    # Authentification
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    
    # Tableaux de bord
    path('dashboard/expediteur/', views.dashboard_expediteur, name='dashboard_expediteur'),
    path('dashboard/agent/', views.dashboard_agent, name='dashboard_agent'),
    path('dashboard/transporteur/', views.dashboard_transporteur, name='dashboard_transporteur'),
    
    # Gestion des colis
    path('colis/creer/', views.creer_colis, name='creer_colis'),
    path('colis/<int:colis_id>/attribuer-transporteur/', views.attribuer_transporteur, name='attribuer_transporteur'),
    path('colis/<int:colis_id>/marquer-livre/', views.marquer_livre, name='marquer_livre'),
    
    # Administration
    path('admin/creer-agent/', views.creer_agent, name='creer_agent'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints supplémentaires
    path('api/colis/', views.api_colis_list, name='api_colis_list'),
    path('api/colis/<int:pk>/', views.api_colis_detail, name='api_colis_detail'),
]