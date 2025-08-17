from django.urls import path
from . import views

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ExpediteurViewSet, DestinataireViewSet, ColisViewSet,
    AgentViewSet, EnregistrementScanViewSet, ScanAPIView,UtilisateurViewSet,ArticleViewSet,
    NotificationViewSet,LivraisonViewSet
)

# Créer un routeur pour les ViewSets
router = DefaultRouter()
# router.register(r'utilisateurs', UtilisateurViewSet)
# router.register(r'expediteurs', ExpediteurViewSet)
# router.register(r'destinataires', DestinataireViewSet)
# router.register(r'colis', ColisViewSet)
# router.register(r'agents', AgentViewSet)
# router.register(r'notifications', NotificationViewSet)
# router.register(r'articles', ArticleViewSet)
# router.register(r'livraisons', LivraisonViewSet)
# router.register(r'scans', EnregistrementScanViewSet)

urlpatterns = [
    path('', include(router.urls)),  # Routes pour CRUD (ex. /api/expediteurs/)
    path('scan/', ScanAPIView.as_view(), name='scan'),  # Route pour l'API de scan
]


# mon_app/api_urls.py
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import DemandeInfosViewSet

router = DefaultRouter()
router.register(r'demandes', DemandeInfosViewSet, basename='demandes')

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

# mon_app/urls.py
from django.urls import path
from .views import demande_page

urlpatterns = [
    path('demande/', demande_page, name='demande-api-page'),
]
