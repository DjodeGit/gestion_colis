from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Expediteur, Agent, Transporteur, Destinataire, Colis
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

class InscriptionExpediteurForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telephone = forms.CharField(max_length=20, required=True)
    adresse = forms.CharField(widget=forms.Textarea, required=True)
    entreprise = forms.CharField(max_length=100, required=False)
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2= forms.CharField(label="Confirmez le mot de passe", widget=forms.PasswordInput)  # au lieu de password2

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'telephone', 'adresse', 'entreprise']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'expediteur'
        if commit:
            user.save()
            Expediteur.objects.create(
                user=user,
                entreprise=self.cleaned_data.get('entreprise', '')
            )
        return user

class InscriptionAgentForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telephone = forms.CharField(max_length=20, required=True)
    zone_operation = forms.CharField(max_length=100, required=True)    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'telephone', 'zone_operation']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'agent'
        if commit:
            user.save()
            Agent.objects.create(
                user=user,
                zone_operation=self.cleaned_data['zone_operation']
            )
        return user

class ConnexionForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))

class DestinataireForm(forms.ModelForm):
    class Meta:
        model = Destinataire
        fields = ['nom_complet', 'telephone', 'adresse', 'ville', 'code_postal']
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 3}),
        }

class ColisForm(forms.ModelForm):
    class Meta:
        model = Colis
        fields = ['description', 'poids', 'dimensions', 'valeur']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, label="Nom complet")
    email = forms.EmailField(label="Email")
    subject = forms.CharField(max_length=150, label="Sujet")
    message = forms.CharField(widget=forms.Textarea, label="Message")



from django.contrib.auth.forms import AuthenticationForm

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "Votre email"
            }
        )
    )


CustomUser = get_user_model()

class AgentCreationForm(forms.ModelForm):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Agent
        fields = ['nom_complet', 'telephone']

    def save(self, commit=True):
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        user = CustomUser.objects.create_user(email=email, password=password)
        agent = super().save(commit=False)
        agent.user = user
        if commit:
            agent.save()
        return agent

class AgentUpdateForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = ['nom_complet', 'telephone']

User = get_user_model()

class AgentRegistrationForm(forms.Form):
    password = forms.CharField(widget=forms.HiddenInput(), required=False)  # Pas visible, généré
    username = forms.CharField(max_length=150, required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)
    telephone = forms.CharField(max_length=20, required=False)  # Nouveau
    zone_operation = forms.CharField(max_length=100, required=False)  # Nouveau
    zone_attribuee = forms.CharField(max_length=100, required=False)  # Nouveau
    class Meta:
        model = User  # Pointe vers CustomUser
        model = Agent
        fields = ['username', 'first_name', 'last_name', 'email','telephone', 'zone_attribuee', 'zone_operation']

    def save(self, commit=True):
        user = super().save(commit=False)
        # Génère un mot de passe aléatoire (12 caractères)
        from django.contrib.auth.hashers import make_password
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        user.set_password(password)
        user.is_staff = False  # Pas admin
        user.is_superuser = False
        if commit:
            user.save()
            # Ajoute au groupe 'Agents' (crée si pas existant)
            group, created = Group.objects.get_or_create(name='Agents')
            user.groups.add(group)
        return user, password  # Retourne pour email
