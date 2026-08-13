from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm
from django import forms
from .models import Profile, Product, Clase
from django.db import models
from .models import Profile, Product, Clase, Modulo, TeacherApplication

class UserInfoForm(forms.ModelForm):
	phone = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Phone'}), required=False)
	address1 = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'address1'}), required=False)
	address2 = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'address2'}), required=False)
	city = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'city'}), required=False)
	state = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'state'}), required=False)
	zipcode = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'zipcode'}), required=False)
	country = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'country'}), required=False)

	class Meta:
		model = Profile
		fields = ('phone', 'address1', 'address2', 'city', 'state', 'zipcode', 'country')

class ChangePasswordForm(SetPasswordForm):
	class Meta:
		model = User
		fields = ['new_password1', 'new_passsword2']

	def __init__(self, *args, **kwargs):
		super(ChangePasswordForm, self).__init__(*args, **kwargs)

	def __init__(self, *args, **kwargs):
		super(ChangePasswordForm, self).__init__(*args, **kwargs)

		self.fields['new_password1'].widget.attrs['class'] = 'form-control'
		self.fields['new_password1'].widget.attrs['placeholder'] = 'Password'
		self.fields['new_password1'].label = ''
		self.fields['new_password1'].help_text = '<ul class="form-text text-muted small"><li>Your password can\'t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can\'t be a commonly used password.</li><li>Your password can\'t be entirely numeric.</li></ul>'

		self.fields['new_password2'].widget.attrs['class'] = 'form-control'
		self.fields['new_password2'].widget.attrs['placeholder'] = 'Confirm Password'
		self.fields['new_password2'].label = ''
		self.fields['new_password2'].help_text = '<span class="form-text text-muted"><small>Enter the same password as before, for verification.</small></span>'
		


class UpdateUserForm(UserChangeForm):
	password = None
	email = forms.EmailField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Email Address'}), required=False)
	first_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'First Name'}), required=False)
	last_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Last Name'}), required=False)
	

	class Meta:
		model = User
		fields = ('username', 'first_name', 'last_name', 'email',)

	def __init__(self, *args, **kwargs):
		super(UpdateUserForm, self).__init__(*args, **kwargs)

		self.fields['username'].widget.attrs['class'] = 'form-control'
		self.fields['username'].widget.attrs['placeholder'] = 'User Name'
		self.fields['username'].label = ''
		self.fields['username'].help_text = '<span class="form-text style="color: white;"><small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span>'

class UpdateProfileForm(forms.ModelForm):
	paypal_email = forms.CharField(label="PayPal Email", max_length=100, required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Last Name'}))
	about_me = forms.CharField(
        label="Sobre ti",
        max_length=350,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Cuéntanos algo sobre ti',
            'rows': 3,  # Controla la altura
            'style': 'resize:none;'  # Opcional: evita que el usuario lo estire
        })
    )
	class Meta:
		
		model = Profile
		fields = ['paypal_email', 'about_me','image',]
		widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control shadow-sm p-3 rounded-3 border-1',
                'style': 'max-width: 100%; height: auto;',
            }),
        }

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['image'].label = ""


class SignUpForm(UserCreationForm):
	email = forms.EmailField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Email Address'}))
	first_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'First Name'}))
	last_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Last Name'}))

	class Meta:
		model = User
		fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

	def __init__(self, *args, **kwargs):
		super(SignUpForm, self).__init__(*args, **kwargs)

		self.fields['username'].widget.attrs['class'] = 'form-control'
		self.fields['username'].widget.attrs['placeholder'] = 'User Name'
		self.fields['username'].label = ''
		self.fields['username'].help_text = '<span class="form-text text-muted"><small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span>'

		self.fields['password1'].widget.attrs['class'] = 'form-control'
		self.fields['password1'].widget.attrs['placeholder'] = 'Password'
		self.fields['password1'].label = ''
		self.fields['password1'].help_text = '<ul class="form-text text-muted small"><li>Your password can\'t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can\'t be a commonly used password.</li><li>Your password can\'t be entirely numeric.</li></ul>'

		self.fields['password2'].widget.attrs['class'] = 'form-control'
		self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'
		self.fields['password2'].label = ''
		self.fields['password2'].help_text = '<span class="form-text text-muted"><small>Enter the same password as before, for verification.</small></span>'


from django import forms
from .models import Comment, CommentResponse

class CommentForm(forms.ModelForm):
	rating = forms.ChoiceField(
        choices=[(i, f'{i} ⭐') for i in range(5, 0, -1)],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label="Calificación"
		)

	class Meta:
		model = Comment
		fields = ['name', 'email', 'rating', 'text']
		widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Tu correo'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': '¿Por qué te interesa esta clase?', 'rows': 3}),
        }

class CommentResponseForm(forms.ModelForm):
    class Meta:
        model = CommentResponse
        fields = ['responder_name', 'response_text']
        widgets = {
            'responder_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre'}),
            'response_text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': '¿Qué te motivó a matricularte?', 'rows': 2}),
        }



class AddProductForm(forms.ModelForm):
    video = forms.FileField(required=False)
    sale_price = forms.DecimalField(required=False)

    class Meta:
        model = Product
        fields = (
            "name", "category", "image", "description", "pay_method",
            "price", "video", 'is_sale', 'sale_price',
            'learning_points', 'requirements', 'target_audience',
            'duration_minutes',
        )
        widgets = {
            'learning_points': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Un punto por línea. Ej:\nDominarás Python desde cero\nCrearás tu primer proyecto real'
            }),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Un requisito por línea'}),
            'target_audience': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Un público por línea'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

class AddClaseForm(forms.ModelForm):
    
    class Meta:
        model = Clase
        fields = ['titleClase','fileClase', 'bannerClase', 'descriptionClase', 'nivel', "productClase", "modulo", "es_preview", "materialClase"]

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        if product:
            self.fields['modulo'].queryset = Modulo.objects.filter(product=product)
        else:
            self.fields['modulo'].queryset = Modulo.objects.none()

class TeacherApplicationForm(forms.ModelForm):
    class Meta:
        model = TeacherApplication
        fields = ['full_name', 'profession', 'specialty', 'experience_years', 'certificate', 'bio']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'profession': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Ingeniero, Licenciado...'}),
            'specialty': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Inglés, Programación...'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Cuéntanos tu experiencia enseñando'}),
        }

class ModuloForm(forms.ModelForm):
    class Meta:
        model = Modulo
        fields = ['titulo', 'orden']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Introducción'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }