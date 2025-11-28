from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

# --- Formulario de Registro ---
class RegisterForm(UserCreationForm):
    """
    Formulario personalizado para el registro de nuevos usuarios.
    
    Hereda de UserCreationForm para manejar la creación segura de contraseñas.
    Añade el campo 'email' como obligatorio y valida su unicidad en el sistema.
    """
    email = forms.EmailField(
        required=True,
        help_text="Usa un correo válido para recuperación."
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        """
        Valida y normaliza el campo de correo electrónico.
        
        Verifica que el email ingresado no exista ya en la base de datos,
        lanzando un error de validación si está duplicado.
        """
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email

# --- Formularios de Perfil ---
class UserUpdateForm(forms.ModelForm):
    """
    Formulario para la actualización de datos básicos del modelo User.
    
    Permite editar nombre de usuario, email, nombre y apellido.
    Incluye widgets personalizados con clases CSS para el tema oscuro.
    """
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
    """
    Formulario para la actualización del modelo Profile (información extendida).
    
    Maneja la subida de la imagen de avatar y la edición de la biografía.
    """
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
    """
    Formulario de autenticación personalizado.
    
    Extiende el formulario base de Django para inyectar clases CSS y estilos
    específicos en el constructor, asegurando consistencia visual con el resto del sitio.
    """
    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario y actualiza los widgets de los campos.
        
        Aplica clases de Bootstrap y estilos personalizados a los campos
        'username' y 'password'.
        """
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