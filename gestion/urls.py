"""
URL configuration for gestion project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include,re_path
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from colis.views import UtilisateurViewSet, ExpediteurViewSet, DemandeInfosViewSet, DestinataireViewSet, ColisViewSet, AgentViewSet, NotificationViewSet, ArticleViewSet,LivraisonViewSet, EnregistrementScanViewSet
                        
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

router = DefaultRouter()
router.register(r'utilisateurs', UtilisateurViewSet)
router.register(r'expediteurs', ExpediteurViewSet)
router.register(r'demandes', DemandeInfosViewSet, basename='demandes')
router.register(r'destinataires', DestinataireViewSet)
router.register(r'colis', ColisViewSet)
router.register(r'agents', AgentViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'articles', ArticleViewSet)
router.register(r'livraisons', LivraisonViewSet)
router.register(r'scans', EnregistrementScanViewSet)


schema_view = get_schema_view(
    openapi.Info(
        title="Gestion Colis API",
        default_version='v1',
        description="Documentation de l'API gestion de colis",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('admin/', admin.site.urls),
    path('', include('colis.urls')), 
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api-auth/', include('rest_framework.urls')),
     path('api/', include(router.urls)),  # Routes pour les APIs CRUD 
]
