from django.test import TestCase

# Create your tests here.
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from .models import Utilisateur, Expediteur, Destinataire, Colis, Agent, EnregistrementScan, Notification, Article, Livraison

class APITestCase(APITestCase):
    def setUp(self):
        # Créer des utilisateurs pour les tests
        self.user_agent = Utilisateur.objects.create_user(
            username='agent1',
            email='agent@example.com',
            password='test123',
            role='agent'
        )
        self.user_exp = Utilisateur.objects.create_user(
            username='exp1',
            email='exp@example.com',
            password='test123',
            role='expediteur'
        )
        self.user_dest = Utilisateur.objects.create_user(
            username='dest1',
            email='dest@example.com',
            password='test123',
            role='destinataire'
        )
        # Créer un expéditeur et un destinataire
        self.expediteur = Expediteur.objects.create(
            utilisateur=self.user_exp,
            qr_code='exp-123'
        )
        self.destinataire = Destinataire.objects.create(
            utilisateur=self.user_dest,
            qr_code='dest-123'
        )
        # Créer un colis
        self.colis = Colis.objects.create(
            description='Test Colis',
            expediteur=self.expediteur,
            destinataire=self.destinataire
        )
        # Créer un agent
        self.agent = Agent.objects.create(utilisateur=self.user_agent)
        # Authentifier l'agent pour les tests
        self.client.force_authenticate(user=self.user_agent)

    def test_create_notification(self):
        """Teste la création d'une notification"""
        data = {
            'utilisateur': str(self.user_exp.id),
            'message': 'Test notification',
            'lu': False
        }
        response = self.client.post('/api/notifications/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Test notification')
        self.assertFalse(response.data['lu'])
        # Vérifier que la notification existe dans la base
        self.assertTrue(Notification.objects.filter(message='Test notification').exists())

    def test_list_notifications(self):
        """Teste la récupération des notifications pour l'utilisateur connecté"""
        Notification.objects.create(
            utilisateur=self.user_agent,
            message='Notification pour agent'
        )
        Notification.objects.create(
            utilisateur=self.user_exp,
            message='Notification pour expéditeur'
        )
        response = self.client.get('/api/notifications/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Vérifier que seules les notifications de l'agent connecté sont retournées
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['message'], 'Notification pour agent')

    def test_update_notification(self):
        """Teste la mise à jour d'une notification (ex. marquer comme lu)"""
        notification = Notification.objects.create(
            utilisateur=self.user_agent,
            message='Notification à lire'
        )
        data = {'lu': True}
        response = self.client.patch(f'/api/notifications/{notification.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['lu'])
        # Vérifier dans la base
        notification.refresh_from_db()
        self.assertTrue(notification.lu)

    def test_create_article(self):
        """Teste la création d'un article et la génération de notifications"""
        data = {
            'titre': 'Test Article',
            'contenu': 'Contenu de test pour article'
        }
        response = self.client.post('/api/articles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['titre'], 'Test Article')
        self.assertEqual(response.data['auteur']['username'], 'agent1')
        # Vérifier que l'article existe
        self.assertTrue(Article.objects.filter(titre='Test Article').exists())
        # Vérifier que les agents ont reçu une notification
        self.assertTrue(
            Notification.objects.filter(
                utilisateur=self.user_agent,
                message__contains='Test Article'
            ).exists()
        )

    def test_list_articles(self):
        """Teste la récupération de la liste des articles"""
        Article.objects.create(
            titre='Article 1',
            contenu='Contenu 1',
            auteur=self.user_agent
        )
        Article.objects.create(
            titre='Article 2',
            contenu='Contenu 2',
            auteur=self.user_exp
        )
        response = self.client.get('/api/articles/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_create_livraison(self):
        """Teste la création d'une livraison et les notifications associées"""
        data = {
            'colis': str(self.colis.id),
            'statut': 'en_route'
        }
        response = self.client.post('/api/livraisons/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['statut'], 'en_route')
        # Vérifier que la livraison existe
        self.assertTrue(Livraison.objects.filter(colis=self.colis).exists())
        # Vérifier que des notifications ont été créées pour l'expéditeur et le destinataire
        self.assertTrue(
            Notification.objects.filter(
                utilisateur=self.user_exp,
                message__contains=self.colis.id
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                utilisateur=self.user_dest,
                message__contains=self.colis.id
            ).exists()
        )

    def test_update_livraison_to_livre(self):
        """Teste la mise à jour d'une livraison à 'livre' et la notification"""
        livraison = Livraison.objects.create(
            colis=self.colis,
            statut='en_route'
        )
        data = {'statut': 'livre'}
        response = self.client.patch(f'/api/livraisons/{livraison.id_livraison}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['statut'], 'livre')
        # Vérifier que la date de livraison a été mise à jour
        livraison.refresh_from_db()
        self.assertIsNotNone(livraison.date_livraison)
        # Vérifier la notification pour le destinataire
        self.assertTrue(
            Notification.objects.filter(
                utilisateur=self.user_dest,
                message__contains='a été livré'
            ).exists()
        )

    def test_scan_with_livraison(self):
        """Teste l'API de scan avec type 'livraison'"""
        data = {
            'qr_expediteur': 'exp-123',
            'qr_destinataire': 'dest-123',
            'agent_id': str(self.agent.id),
            'type_scan': 'livraison'
        }
        response = self.client.post('/api/scan/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Scan enregistré')
        # Vérifier que le scan a été créé
        self.assertTrue(EnregistrementScan.objects.filter(colis=self.colis).exists())
        # Vérifier que la livraison a été créée/mise à jour
        self.assertTrue(Livraison.objects.filter(colis=self.colis, statut='livre').exists())
        # Vérifier les notifications
        self.assertTrue(
            Notification.objects.filter(
                utilisateur=self.user_exp,
                message__contains='scanné pour livraison'
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                utilisateur=self.user_dest,
                message__contains='scanné pour livraison'
            ).exists()
        )
        # Vérifier que le statut du colis a été mis à jour
        self.colis.refresh_from_db()
        self.assertEqual(self.colis.statut, 'livre')