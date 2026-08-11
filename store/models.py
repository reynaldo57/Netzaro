from django.db import models
import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.text import slugify
from django.utils import timezone
# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    paypal_email = models.EmailField(max_length=255, null=True, blank=True)
    about_me = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='uploads/product', default='profile_images/default.jpg')
    date_modified = models.DateTimeField(User, auto_now=True)
    phone = models.CharField(max_length=200, blank=True)
    address1 = models.CharField(max_length=200, blank=True)
    address2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=200, blank=True)
    zipcode = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=200, blank=True)
    old_cart = models.CharField(max_length=5000, blank=True, null=True)

    TEACHER_STATUS_CHOICES = [
        ('none', 'No solicitado'),
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ]
    teacher_request_status = models.CharField(
        max_length=10, choices=TEACHER_STATUS_CHOICES, default='none'
    )
    teacher_request_date = models.DateTimeField(null=True, blank=True)


    def get_profile_picture(self):
        try:
            return self.image.url
        except:
            return ""


    def __str__(self):
        return self.user.username
    
    
#Create a user Profile by default when user singup
def create_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()
#automte the profile thing
post_save.connect(create_profile, sender=User)

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'categories'
    
class Customer(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=10)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
class Product(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    price = models.DecimalField(default=0, decimal_places=2, max_digits=6)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    description = models.CharField(max_length=250, default='', blank=True, null=True)
    image = models.ImageField(upload_to='uploads/product')
    is_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(default=0, decimal_places=2, max_digits=6, null=True, blank=True)
    pay_method = models.CharField(max_length=250, null=True)
    video = models.FileField(upload_to="video", null=True)
    created_day = models.DateTimeField(default=timezone.now)

    learning_points = models.TextField(
        blank=True, default='',
        verbose_name="Lo que aprenderás",
        help_text="Un punto por línea"
    )
    requirements = models.TextField(
        blank=True, default='',
        verbose_name="Requisitos previos",
        help_text="Un requisito por línea"
    )
    target_audience = models.TextField(
        blank=True, default='',
        verbose_name="Dirigido a",
        help_text="Un público por línea"
    )
    language = models.CharField(
        max_length=50, blank=True, default='Español',
        verbose_name="Idioma"
    )
    duration_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name="Duración total (minutos)"
    )

    # --- Helpers para la plantilla ---
    def learning_points_list(self):
        return [p.strip() for p in self.learning_points.splitlines() if p.strip()]

    def requirements_list(self):
        return [r.strip() for r in self.requirements.splitlines() if r.strip()]

    def target_audience_list(self):
        return [a.strip() for a in self.target_audience.splitlines() if a.strip()]

    def total_lessons(self):
        return self.clases.count()

    def duration_display(self):
        h, m = divmod(self.duration_minutes, 60)
        return f"{h}h {m}min" if h else f"{m}min"

    def students_count(self):
        from payment.models import OrderItem
        return OrderItem.objects.filter(
            product=self, order__paid=True
        ).values('user').distinct().count()

    def average_rating(self):
        from django.db.models import Avg
        return self.product_comment.filter(
            rating__isnull=False
        ).aggregate(avg=Avg('rating'))['avg'] or 0

    def average_rating_rounded(self):
        return round(self.average_rating())

    def rating_count(self):
        return self.product_comment.filter(rating__isnull=False).count()


    def __str__(self):
        return self.name

    def grant_access(self, user):
        if not user or not user.is_authenticated:
            return
        for clase in self.clases.all():
            clase.marcar_como_pagada(user)
    
class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    address = models.CharField(max_length=100, default='', blank=True)
    phone = models.CharField(max_length=20, default='', blank=True)
    date = models.DateField(default=datetime.datetime.today)
    status = models.BooleanField(default=False)

    def __str__(self):
        return self.product
    

class Comment(models.Model):
    user = models.ForeignKey(
        User,
        related_name='user_comment',
        on_delete=models.CASCADE, null=True
    )
    product = models.ForeignKey(
        Product,
        related_name='product_comment',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100, null=True)
    email = models.EmailField(null=True)  # Nuevo campo 'email'
    text = models.TextField(null=True)
    time_begin = models.DateTimeField(null=True)  # Nuevo campo 'time_begin'
    time_final = models.DateTimeField(null=True)  # Nuevo campo 'time_final'
    topic = models.CharField(max_length=200, null=True)  # Nuevo campo 'topic'
    created_date = models.DateTimeField(auto_now_add=True)
    rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name="Calificación"
    )

    class Meta:
        ordering = ['-created_date']  # 🔥 Esto asegura el orden DESC en toda la app

    def __str__(self) -> str:
        return self.text
    

class CommentResponse(models.Model):
    comment = models.ForeignKey(Comment, related_name='responses', on_delete=models.CASCADE)
    responder_name = models.CharField(max_length=100)
    response_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.responder_name} respondió a {self.comment.name}"


class Clase(models.Model):
    user = models.ForeignKey(
        User, related_name='user_clase', on_delete=models.CASCADE
    )
    productClase = models.ForeignKey(  # 🔥 Relación con Blog
        Product, related_name='clases', on_delete=models.CASCADE, default=1  
    )
    titleClase = models.CharField(max_length=250)
    slugClase = models.SlugField(null=True, blank=True)
    fileClase = models.FileField(upload_to='files', verbose_name="Archivo")
    bannerClase = models.ImageField(upload_to='clase_banners')
    descriptionClase = models.CharField(max_length=450)
    
    nivel = models.CharField(  # 🔥 Campo para Nivel
        max_length=20,
        choices=[("Basico", "Básico"), ("Intermedio", "Intermedio"), ("Avanzado", "Avanzado")],
        default="Basico"
    )

    class_date = models.DateField(auto_now_add=True)

      # 🔥 Nuevos campos para control de pagos
    usuarios_pagados = models.ManyToManyField(
        User, 
        related_name='clases_pagadas', 
        blank=True,
        help_text="Usuarios que han pagado por esta clase"
    )
    es_preview = models.BooleanField(
        default=False,
        verbose_name="Vista previa gratuita",
        help_text="Si está marcado, cualquier visitante puede verla sin comprar"
    )

    def __str__(self) -> str:
        return f"{self.titleClase} - {self.nivel}"

    def save(self, *args, **kwargs):
        if not self.slugClase:
            self.slugClase = slugify(self.titleClase)
        super().save(*args, **kwargs)

 # 🔥 Método para verificar si un usuario ha pagado
    def usuario_ha_pagado(self, usuario):
        """Verifica si el usuario ha pagado por esta clase"""
        if not usuario.is_authenticated:
            return False
        return self.usuarios_pagados.filter(id=usuario.id).exists()
    
    # 🔥 Método para marcar clase como pagada por un usuario
    def marcar_como_pagada(self, usuario):
        """Marca esta clase como pagada por el usuario"""
        if usuario.is_authenticated and not self.usuario_ha_pagado(usuario):
            self.usuarios_pagados.add(usuario)
    
    # 🔥 Método para saber si requiere pago
    def requiere_pago(self):
        """Solo las clases avanzadas requieren pago"""
        return self.nivel == "Avanzado"


class TeacherApplication(models.Model):
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name='teacher_application'
    )
    full_name = models.CharField(max_length=150, verbose_name="Nombre completo")
    profession = models.CharField(max_length=150, verbose_name="Profesión")
    specialty = models.CharField(max_length=150, verbose_name="Materia o especialidad a enseñar")
    experience_years = models.PositiveIntegerField(verbose_name="Años de experiencia", default=0)
    certificate = models.FileField(upload_to='teacher_certificates', verbose_name="Certificado")
    bio = models.TextField(max_length=1000, verbose_name="Cuéntanos sobre tu experiencia")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Solicitud de {self.full_name} ({self.profile.user.username})"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f'{self.user.username} - {self.product.name}'