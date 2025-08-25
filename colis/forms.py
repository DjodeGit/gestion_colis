from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Expediteur, Agent, Transporteur, Destinataire, Colis

class InscriptionExpediteurForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telephone = forms.CharField(max_length=20, required=True)
    adresse = forms.CharField(widget=forms.Textarea, required=True)
    entreprise = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'telephone', 'adresse', 'entreprise']
    
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