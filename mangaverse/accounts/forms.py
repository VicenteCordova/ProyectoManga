from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

# --- Formulario de Registro ---
class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Usa un correo válido para recuperación."
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email

# --- Formularios de Perfil ---
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'Usuario'}),
            'email': forms.EmailInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'Apellido'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control bg-dark text-white border-secondary', 
                'rows': 3, 
                'placeholder': 'Cuéntanos qué mangas te gustan...'
            }),
            'avatar': forms.FileInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
        }

# --- Formulario de Login Personalizado ---
class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Estilo base para inputs modernos oscuros
        base_class = 'form-control form-control-lg bg-dark-input text-white border-0 shadow-none'
        
        self.fields['username'].widget.attrs.update({
            'class': base_class,
            'placeholder': 'Usuario',
            'style': 'border-radius: 12px; padding: 1rem;' 
        })
        self.fields['password'].widget.attrs.update({
            'class': base_class,
            'placeholder': 'Contraseña',
            'style': 'border-radius: 12px; padding: 1rem;'
        })