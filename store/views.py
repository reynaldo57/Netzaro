from django.shortcuts import render, redirect, get_object_or_404
from .models import (Product, Category, Profile, Comment, CommentResponse, Clase, Wishlist, Modulo, Progreso, LeccionCompletada, Quiz, Pregunta, IntentoQuiz, Tarea, EntregaTarea, Certificado, Coupon)
from cart.cart import Cart
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm, UpdateProfileForm, CommentForm, CommentResponseForm, AddProductForm, AddClaseForm, TeacherApplicationForm
from payment.forms import ShippingForm
from payment.models import ShippingAddress
from django import forms
from django.db.models import Q
import json
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count

import os
from django.conf import settings
from django.http import HttpResponse
from .forms import ModuloForm, EntregaTareaForm, RevisionEntregaForm, QuizForm, PreguntaForm, OpcionFormSet, TareaForm, CouponForm

def search(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    nivel = request.GET.get('nivel', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    order = request.GET.get('order', 'relevance')

    results = Product.objects.none()

    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

        if category_id:
            results = results.filter(category_id=category_id)

        if nivel:
            results = results.filter(clases__nivel=nivel)

        if price_min:
            try:
                results = results.filter(price__gte=float(price_min))
            except ValueError:
                pass

        if price_max:
            try:
                results = results.filter(price__lte=float(price_max))
            except ValueError:
                pass

        results = results.distinct()

        results = results.annotate(
            num_ventas=Count(
                'orderitem',
                filter=Q(orderitem__order__paid=True),
                distinct=True
            )
        ).distinct()

        order_map = {
            'price_asc': 'price',
            'price_desc': '-price',
            'newest': '-created_day',
            'name_asc': 'name',
            'popularity': '-num_ventas',
            # 'rating': '-avg_rating',  # activar cuando exista el modelo de calificaciones
        }
        if order in order_map:
            results = results.order_by(order_map[order])

    paginator = Paginator(results, 12)  # 12 cursos por página
    page_obj = paginator.get_page(request.GET.get('page'))

    if query and not results.exists():
        messages.info(request, "No se encontraron cursos para tu búsqueda.")


    return render(request, "search.html", {
        'searched': page_obj,
        'query': query,
        'categories': Category.objects.all(),
        'selected_category': category_id,
        'selected_nivel': nivel,
        'price_min': price_min,
        'price_max': price_max,
        'selected_order': order,
    })
    
def update_info(request):
    if request.user.is_authenticated:
        #Get current user
        current_user = Profile.objects.get(user__id=request.user.id)
        #Get current user's shipping Info
        shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
        #Get original user form
        form = UserInfoForm(request.POST or None, instance=current_user)
        #Get user's shipping form
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
        if form.is_valid() or shipping_form.is_valid():
            #save original form
            form.save()
            #save shipping form
            shipping_form.save()
            messages.success(request, "Your Info Has Been Updated")
            return redirect('index')
        return render(request,"update_info.html", {'form':form, 'shipping_form':shipping_form})
    else:
        messages.success(request, "You must be logged in to access that page")
        return redirect('index')

def update_password(request):
    if request.user.is_authenticated:
        current_user = request.user
        if request.method == 'POST':
            form = ChangePasswordForm(current_user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your Password has been updated, Loggin again...")
                login(request, current_user)
                return redirect('update_user')
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
                    return redirect('update_password')
        else:
            form = ChangePasswordForm(current_user)
            return render(request, "update_password.html", {'form': form})
    else:
        messages.success(request, "You must be loogged in to view that page...")
        return redirect('index')
    

def update_user(request):
    if request.user.is_authenticated:
        current_user = request.user
        profile = current_user.profile
        user_form = UpdateUserForm(request.POST or None, instance=current_user)
        profile_form = UpdateProfileForm(request.POST or None, request.FILES or None, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            login(request, current_user)
            messages.success(request, "User Has Been Updated")
            return redirect('index')
        return render(request,"update_user.html", {'user_form':user_form, 'profile_form': profile_form,})
    else:
        messages.success(request, "You must be logged in to access that page")
        return redirect('index')

@login_required(login_url='login')
def request_teacher(request):
    profile = request.user.profile
    if profile.teacher_request_status == 'approved':
        messages.info(request, "Ya tienes una cuenta de profesor.")
        return redirect('update_user')
    if profile.teacher_request_status == 'pending':
        messages.info(request, "Ya tienes una solicitud pendiente de revisión.")
        return redirect('update_user')
    application = getattr(profile, 'teacher_application', None)
    form = TeacherApplicationForm(request.POST or None, request.FILES or None, instance=application)

    if request.method == "POST" and form.is_valid():
        application = form.save(commit=False)
        application.profile = profile
        application.save()
        profile.teacher_request_status = 'pending'
        profile.teacher_request_date = timezone.now()
        profile.save()
        messages.success(request, "Tu solicitud para ser profesor fue enviada.")
        return redirect('update_user')

    return render(request, 'request_teacher.html', {'form': form})


@login_required(login_url='login')
def teacher_requests_dash(request):
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para ver esta página.")
        return redirect('index')

    if request.method == "POST":
        profile = get_object_or_404(Profile, id=request.POST.get('profile_id'))
        if request.POST.get('decision') == 'approve':
            profile.teacher_request_status = 'approved'
        else:
            profile.teacher_request_status = 'rejected'
        profile.save()
        messages.success(request, "Solicitud actualizada")
        return redirect('teacher_requests_dash')

    pending_requests = Profile.objects.filter(teacher_request_status='pending').select_related('teacher_application', 'user')
    return render(request, 'teacher_requests_dash.html', {"pending_requests": pending_requests})


def category_summary(request):
    categories = Category.objects.all()
    return render(request, 'category_summary.html', {"categories":categories})

def category(request,foo):
    #replace hypens whit spaces
    foo = foo.replace('-', '')
    #grab the category from the url
    try:
        #look up the category
        category = Category.objects.get(name=foo)
        products = Product.objects.filter(category=category)
        return render(request, 'category.html', {'products': products, 'category':category})
    except:
        messages.success(request, ("That category Doest exist"))
        return redirect('index')



def product(request, pk):
    product = get_object_or_404(Product, id=pk)
    comments = Comment.objects.filter(product=product)
    curriculum = [
    ('Versión gratuita', Clase.objects.filter(productClase=product, nivel='Gratis')), 
    ('Versión de pago', Clase.objects.filter(productClase=product, nivel='Pago')),
    ]
    instructor_courses_count = Product.objects.filter(user=product.user).count()
    can_review = request.user.is_authenticated and product.usuario_matriculado(request.user)
    is_instructor = request.user.is_authenticated and (
        request.user == product.user or request.user.is_superuser
    )

    # Reseña (crear) — solo estudiantes matriculados (compra confirmada)
    if request.method == 'POST' and 'comment_form' in request.POST:
        if not request.user.is_authenticated:
            messages.error(request, "Inicia sesión para dejar una reseña.")
            return redirect('login')
        if not product.usuario_matriculado(request.user):
            messages.error(request, "Solo los estudiantes matriculados pueden dejar una reseña.")
            return redirect('product', pk=pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.product = product
            comment.user = request.user
            comment.name = request.user.get_full_name() or request.user.username
            comment.email = request.user.email
            comment.save()
            return redirect('product', pk=pk)
    else:
        form = CommentForm()
        
    # Respuesta a reseña — solo el instructor dueño del curso (o superusuario)
    if request.method == 'POST' and 'respuesta_form' in request.POST:
        if not is_instructor:
            messages.error(request, "Solo el instructor del curso puede responder reseñas.")
            return redirect('product', pk=pk)
        comment_id = request.POST.get('comment_id')
        comment_obj = get_object_or_404(Comment, id=comment_id, product=product)
        response_form = CommentResponseForm(request.POST)
        if response_form.is_valid():
            response = response_form.save(commit=False)
            response.comment = comment_obj
            response.responder_name = request.user.get_full_name() or request.user.username
            response.save()
            messages.success(request, "Respuesta publicada.")
            return redirect('product', pk=pk)
    else:
        response_form = CommentResponseForm()

    return render(request, 'product.html', {
        'product': product,
        'form': form,
        'comments': comments,
        'response_form': response_form,
        'curriculum': curriculum,
        'instructor_courses_count': instructor_courses_count,
        'can_review': can_review,
        'is_instructor': is_instructor,
    })



@login_required(login_url='login')
def add_product(request):
    if not (request.user.is_superuser or request.user.profile.teacher_request_status == 'approved'):
        messages.error(request, "Necesitas una cuenta de profesor aprobada para crear cursos.")
        return redirect('update_user')
    form = AddProductForm()
    categories = Category.objects.all()

    if request.method == "POST":
        form = AddProductForm(request.POST, request.FILES)
        if form.is_valid():
            user = get_object_or_404(User, id=request.user.id)
            category = get_object_or_404(Category, pk=request.POST['category'])
            product = form.save(commit=False)
            product.user = user
            product.category = category
            product.user = request.user
            product.save()

            messages.success(request, "Product added successfully")
            return redirect('product', pk=product.id)
        else:
            print(form.errors)

    context = {
        "form": form,
        "categories": categories,
    }
    return render(request, 'add_product.html', context)



@login_required(login_url='login')
def my_products(request):
    queryset = Product.objects.filter(user=request.user).order_by('-created_day')
    delete = request.GET.get('delete', None)
    if delete:
        product = get_object_or_404(Product, id=delete)
        
        if request.user.id != product.user.id:
            return redirect('index')

        product.delete()
        messages.success(request, "Your blog has been deleted!")
        return redirect('my_products')

    context = {
        
        "queryset": queryset,
    }
    
    return render(request, 'my_products.html', context)


@login_required(login_url='login')
def update_product(request, id):
    product = get_object_or_404(Product, id=id)
    form = AddProductForm(instance=product)
    if request.method == "POST":
        form = AddProductForm(request.POST, request.FILES, instance=product)
        
        if form.is_valid():
            
            if request.user.id != product.user.id:
                return redirect('index')

            user = get_object_or_404(User, id=request.user.id)
            category = get_object_or_404(Category, pk=request.POST['category'])
            product = form.save(commit=False)
            product.user = user
            product.category = category

            
            product.save()

            messages.success(request, "Curso actualizado correctamente")
            return redirect('product', pk=product.id)
        else:
            print(form.errors)


    context = {
        "form": form,
        "product": product,
        "categories": Category.objects.all()
    }
    return render(request, 'update_product.html', context)




def index(request):
    products = Product.objects.all().order_by('-created_day')[:24]
    return render(request, 'index.html', {'products':products})

def about(request):
    return render(request, 'about.html')

def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            current_user =Profile.objects.get(user__id=request.user.id)
            saved_cart = current_user.old_cart
            
            if saved_cart:
                #Convert to dictionary usig Json
                converted_cart = json.loads(saved_cart)
                # Add the loades cart dictionary to our session
                #Get the cart
                cart = Cart(request)
                #loop thru the cart and add the items from the database
                for key,value in converted_cart.items():
                    cart.db_add(product=key,  quantity=value)
            messages.success(request, ('You have been Logged In'))
            return redirect('index')
        else:
            messages.success(request, ('There was an error, try again'))
            return redirect('login')
    else:
        return render(request, 'login.html')
    

def logout_user(request):
    logout(request)
    messages.success(request, ("You have been logout"))
    return redirect('index')

def register_user(request):
    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            #log in user
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ("UserName Created - please fill out yor User Info Below"))
            return redirect('update_info')
        else:
            messages.success(request, ("There was an error, try again.!"))
            return redirect('register')
    else:
        return render(request, 'register.html', {'form': form})

# Create your views here.
def view_user_information(request, username):
    account = get_object_or_404(User, username=username)
    product_user = Product.objects.filter(user=account).order_by('-id')
    profile = account.profile


    if request.user.is_authenticated:
        
        if request.user.id == account.id:
            return redirect("update_user")

        

    context = {
        "account": account,
        "product_user": product_user,
        "profile": profile 
    }
    return render(request, "user_information.html", context)


@login_required(login_url='login')
def add_clase(request):
    productClase_id = request.GET.get('productClase')  # Obtener blog de la URL
    products = Product.objects.all()
    if not productClase_id:
        messages.error(request, "No productclase ID provided.")
        return redirect('index')

    productClase = get_object_or_404(Product, id=productClase_id)  # Obtener el Product

     # 🚫 Verificación de permiso: solo el creador puede agregar clases
    if productClase.user != request.user:
        messages.error(request, "No tienes permiso para agregar clases a este producto.")
        return redirect('index')

    # Asegúrate de pasar el `productClase` al formulario en la inicialización
    formClase = AddClaseForm(initial={'productClase': productClase}, product=productClase)

    if request.method == "POST":
        formClase = AddClaseForm(request.POST, request.FILES, product=productClase)
        if formClase.is_valid():
            clase = formClase.save(commit=False)
            clase.user = request.user  # Asignar usuario
            clase.productClase = productClase  # Asegurar que la clase esté relacionada con el blog
            clase.save()

            messages.success(request, "Clase added successfully")
            return redirect('index',)
        else:
            print(formClase.errors)  # Para ver qué está fallando

            
    context = {
        "formClase": formClase,
        "productClase": productClase,
        "products": products,
        "modulos": Modulo.objects.filter(product=productClase),
    }
    return render(request, 'add_clase.html', context)




def product_detail_view(request, id):
    product = get_object_or_404(Product, id=id)

    clases_gratis = Clase.objects.filter(productClase=product, nivel="Gratis")
    clases_pago   = Clase.objects.filter(productClase=product, nivel="Pago")

    recommended_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id).annotate(
        num_ventas=Count('orderitem', filter=Q(orderitem__order__paid=True), distinct=True)
    ).order_by('-num_ventas', '-created_day')[:4]
    # 🔥 Obtener IDs de clases pagadas por el usuario
    clases_pagadas = []
    
    if request.user.is_authenticated:
        # Usuarios logueados: obtener desde la relación ManyToMany
        clases_pagadas = [
            str(clase.id) for clase in request.user.clases_pagadas.filter(productClase=product)
        ]
    else:
        # Usuarios anónimos: obtener desde sesión
        clases_pagadas = request.session.get('clases_pagadas', [])

    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    from payment.models import OrderItem
    acceso_completo_comprado = False
    if request.user.is_authenticated:
        acceso_completo_comprado = OrderItem.objects.filter(
            product=product, user=request.user, order__paid=True
        ).exists()

    context = {
        "product": product,
        "clases_gratis": clases_gratis,
        "clases_pago": clases_pago,
        "clases_pagadas": clases_pagadas,
        "recommended_products": recommended_products,
        "in_wishlist": in_wishlist,
        "acceso_completo_comprado": acceso_completo_comprado,
    }
    return render(request, 'product_detail.html', context)


@login_required(login_url='login')
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        messages.success(request, "Curso quitado de tu lista de deseos")
    else:
        messages.success(request, "Curso guardado en tu lista de deseos")
    return redirect(request.META.get('HTTP_REFERER', 'index'))

@login_required(login_url='login')
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'wishlist.html', {'items': items})

@login_required(login_url='login')
def ver_clase(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    product = clase.productClase

    if not clase.acceso_permitido(request.user):
        messages.error(request, "No tienes acceso a esta clase todavía.")
        return redirect('product_detail', id=product.id)

    # Guarda/actualiza el punto de avance ("continuar donde lo dejaste")
    Progreso.objects.update_or_create(
        user=request.user, product=product, defaults={'clase': clase}
    )

    modulos = Modulo.objects.filter(product=product).prefetch_related('clases')
    sin_modulo = Clase.objects.filter(productClase=product, modulo__isnull=True)

    completadas_ids = set(
        LeccionCompletada.objects.filter(user=request.user, clase__productClase=product)
        .values_list('clase_id', flat=True)
    )

    todas_las_clases = list(Clase.objects.filter(productClase=product).order_by('modulo__orden', 'id'))
    idx = todas_las_clases.index(clase)
    anterior = todas_las_clases[idx - 1] if idx > 0 else None
    siguiente = todas_las_clases[idx + 1] if idx < len(todas_las_clases) - 1 else None

    context = {
        "product": product,
        "clase": clase,
        "modulos": modulos,
        "sin_modulo": sin_modulo,
        "completadas_ids": completadas_ids,
        "es_completada": clase.id in completadas_ids,
        "anterior": anterior,
        "siguiente": siguiente,
        "porcentaje": product.porcentaje_completado(request.user),
        "quizzes": product.quizzes.all(),
        "tareas": product.tareas.all(),
        "certificado_disponible": product.certificado_disponible(request.user),
    }
    return render(request, 'ver_clase.html', context)


@login_required(login_url='login')
def toggle_leccion_completada(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    obj, created = LeccionCompletada.objects.get_or_create(user=request.user, clase=clase)
    if not created:
        obj.delete()
        messages.success(request, "Lección desmarcada")
    else:
        messages.success(request, "¡Lección completada!")
    return redirect('ver_clase', clase_id=clase.id)


@login_required(login_url='login')
def continuar_curso(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    progreso = Progreso.objects.filter(user=request.user, product=product).first()
    if progreso:
        return redirect('ver_clase', clase_id=progreso.clase.id)

    primera = Clase.objects.filter(productClase=product).order_by('modulo__orden', 'id').first()
    if primera:
        return redirect('ver_clase', clase_id=primera.id)

    messages.info(request, "Este curso todavía no tiene clases.")
    return redirect('product_detail', id=product.id)

def service_worker(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')
    with open(sw_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/javascript')

@login_required(login_url='login')
def add_modulo(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.user != request.user:
        messages.error(request, "No tienes permiso para agregar módulos a este curso.")
        return redirect('index')

    form = ModuloForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        modulo = form.save(commit=False)
        modulo.product = product
        modulo.save()
        messages.success(request, "Módulo agregado")
        return redirect('add_modulo', product_id=product.id)

    modulos = Modulo.objects.filter(product=product)
    return render(request, 'add_modulo.html', {'form': form, 'product': product, 'modulos': modulos})

@login_required(login_url='login')
def tomar_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    product = quiz.product

    if not product.usuario_matriculado(request.user):
        messages.error(request, "Debes comprar el curso para rendir esta evaluación.")
        return redirect('product_detail', id=product.id)

    preguntas = quiz.preguntas.prefetch_related('opciones')

    if request.method == 'POST':
        total = preguntas.count()
        correctas = 0
        for pregunta in preguntas:
            opcion_id = request.POST.get(f'pregunta_{pregunta.id}')
            if opcion_id and pregunta.opciones.filter(id=opcion_id, es_correcta=True).exists():
                correctas += 1
        puntaje = round((correctas / total) * 100) if total else 0
        intento = IntentoQuiz.objects.create(
            user=request.user, quiz=quiz, puntaje=puntaje,
            aprobado=puntaje >= quiz.nota_minima_aprobatoria
        )
        return redirect('resultado_quiz', intento_id=intento.id)

    return render(request, 'tomar_quiz.html', {'quiz': quiz, 'preguntas': preguntas, 'product': product})


@login_required(login_url='login')
def resultado_quiz(request, intento_id):
    intento = get_object_or_404(IntentoQuiz, id=intento_id, user=request.user)
    return render(request, 'resultado_quiz.html', {'intento': intento})


@login_required(login_url='login')
def entregar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    product = tarea.product

    if not product.usuario_matriculado(request.user):
        messages.error(request, "Debes comprar el curso para entregar esta tarea.")
        return redirect('product_detail', id=product.id)

    entrega = EntregaTarea.objects.filter(tarea=tarea, user=request.user).first()

    if request.method == 'POST':
        form = EntregaTareaForm(request.POST, request.FILES, instance=entrega)
        if form.is_valid():
            nueva_entrega = form.save(commit=False)
            nueva_entrega.tarea = tarea
            nueva_entrega.user = request.user
            nueva_entrega.estado = 'pendiente'
            nueva_entrega.feedback_docente = ''
            nueva_entrega.save()
            messages.success(request, "Tarea entregada correctamente.")
            return redirect('entregar_tarea', tarea_id=tarea.id)
    else:
        form = EntregaTareaForm(instance=entrega)

    return render(request, 'entregar_tarea.html', {
        'tarea': tarea, 'form': form, 'entrega': entrega, 'product': product,
    })


@login_required(login_url='login')
def revisar_entregas(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.user != request.user:
        messages.error(request, "No tienes permiso para revisar las entregas de este curso.")
        return redirect('index')

    entregas = EntregaTarea.objects.filter(tarea__product=product).select_related('tarea', 'user')
    return render(request, 'revisar_entregas.html', {'product': product, 'entregas': entregas})


@login_required(login_url='login')
def calificar_entrega(request, entrega_id):
    entrega = get_object_or_404(EntregaTarea, id=entrega_id)
    if entrega.tarea.product.user != request.user:
        messages.error(request, "No tienes permiso para calificar esta entrega.")
        return redirect('index')

    if request.method == 'POST':
        form = RevisionEntregaForm(request.POST, instance=entrega)
        if form.is_valid():
            form.save()
            messages.success(request, "Entrega calificada.")
    return redirect('revisar_entregas', product_id=entrega.tarea.product.id)


@login_required(login_url='login')
def generar_certificado(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not product.certificado_disponible(request.user):
        messages.error(request, "Todavía no cumples los requisitos para obtener el certificado de este curso.")
        return redirect('continuar_curso', product_id=product.id)

    certificado, _ = Certificado.objects.get_or_create(user=request.user, product=product)
    return render(request, 'certificado.html', {'certificado': certificado})


def verificar_certificado(request, codigo):
    certificado = Certificado.objects.filter(codigo=codigo).first()
    return render(request, 'verificar_certificado.html', {'certificado': certificado, 'codigo': codigo})


@login_required(login_url='login')
def add_quiz(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.user != request.user:
        messages.error(request, "No tienes permiso para agregar evaluaciones a este curso.")
        return redirect('index')

    form = QuizForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        quiz = form.save(commit=False)
        quiz.product = product
        quiz.save()
        messages.success(request, "Quiz creado. Ahora agrega sus preguntas.")
        return redirect('add_pregunta', quiz_id=quiz.id)

    quizzes = Quiz.objects.filter(product=product)
    return render(request, 'add_quiz.html', {'form': form, 'product': product, 'quizzes': quizzes})


@login_required(login_url='login')
def add_pregunta(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.product.user != request.user:
        messages.error(request, "No tienes permiso para editar este quiz.")
        return redirect('index')

    form = PreguntaForm(request.POST or None)
    formset = OpcionFormSet(request.POST or None, prefix='opciones')

    if request.method == "POST" and form.is_valid() and formset.is_valid():
        pregunta = form.save(commit=False)
        pregunta.quiz = quiz
        pregunta.save()
        formset.instance = pregunta
        formset.save()
        messages.success(request, "Pregunta agregada")
        return redirect('add_pregunta', quiz_id=quiz.id)

    preguntas = quiz.preguntas.prefetch_related('opciones')
    return render(request, 'add_pregunta.html', {
        'form': form, 'formset': formset, 'quiz': quiz, 'preguntas': preguntas,
    })


@login_required(login_url='login')
def add_tarea(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.user != request.user:
        messages.error(request, "No tienes permiso para agregar tareas a este curso.")
        return redirect('index')

    form = TareaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        tarea = form.save(commit=False)
        tarea.product = product
        tarea.save()
        messages.success(request, "Tarea agregada")
        return redirect('add_tarea', product_id=product.id)

    tareas = Tarea.objects.filter(product=product)
    return render(request, 'add_tarea.html', {'form': form, 'product': product, 'tareas': tareas})

@login_required(login_url='login')
def eliminar_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.product.user != request.user:
        messages.error(request, "No tienes permiso para eliminar este quiz.")
        return redirect('index')
    if request.method != 'POST':
        return redirect('add_quiz', product_id=quiz.product.id)

    product_id = quiz.product.id
    quiz.delete()
    messages.success(request, "Quiz eliminado.")
    return redirect('add_quiz', product_id=product_id)


@login_required(login_url='login')
def eliminar_pregunta(request, pregunta_id):
    pregunta = get_object_or_404(Pregunta, id=pregunta_id)
    if pregunta.quiz.product.user != request.user:
        messages.error(request, "No tienes permiso para eliminar esta pregunta.")
        return redirect('index')
    if request.method != 'POST':
        return redirect('add_pregunta', quiz_id=pregunta.quiz.id)

    quiz_id = pregunta.quiz.id
    pregunta.delete()
    messages.success(request, "Pregunta eliminada.")
    return redirect('add_pregunta', quiz_id=quiz_id)


@login_required(login_url='login')
def eliminar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    if tarea.product.user != request.user:
        messages.error(request, "No tienes permiso para eliminar esta tarea.")
        return redirect('index')
    if request.method != 'POST':
        return redirect('add_tarea', product_id=tarea.product.id)

    product_id = tarea.product.id
    tarea.delete()
    messages.success(request, "Tarea eliminada.")
    return redirect('add_tarea', product_id=product_id)

@login_required(login_url='login')
def instructor_dashboard(request):
    if not (request.user.is_superuser or request.user.profile.teacher_request_status == 'approved'):
        messages.error(request, "Necesitas una cuenta de profesor aprobada para ver el panel de analítica.")
        return redirect('update_user')

    from django.db.models import Sum
    from payment.models import OrderItem

    productos = Product.objects.filter(user=request.user).order_by('-created_day')

    data = []
    total_ingresos = 0
    total_inscritos = 0
    for product in productos:
        items_pagados = OrderItem.objects.filter(product=product, order__paid=True)
        ingresos = items_pagados.aggregate(suma=Sum('price'))['suma'] or 0
        inscritos = items_pagados.values('user').distinct().count()
        total_ingresos += ingresos
        total_inscritos += inscritos
        data.append({
            'product': product,
            'ingresos': ingresos,
            'inscritos': inscritos,
            'rating': product.average_rating(),
            'rating_count': product.rating_count(),
        })

    context = {
        'data': data,
        'total_ingresos': total_ingresos,
        'total_inscritos': total_inscritos,
    }
    return render(request, 'instructor_dashboard.html', context)

@login_required(login_url='login')
def manage_coupons(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.user != request.user and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para gestionar cupones de este curso.")
        return redirect('index')

    form = CouponForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        coupon = form.save(commit=False)
        coupon.product = product
        coupon.code = coupon.code.upper()
        coupon.save()
        messages.success(request, "Cupón creado")
        return redirect('manage_coupons', product_id=product.id)

    coupons = Coupon.objects.filter(product=product).order_by('-created_date')
    return render(request, 'manage_coupons.html', {'form': form, 'product': product, 'coupons': coupons})


@login_required(login_url='login')
def eliminar_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if coupon.product.user != request.user and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para eliminar este cupón.")
        return redirect('index')
    if request.method != 'POST':
        return redirect('manage_coupons', product_id=coupon.product.id)

    product_id = coupon.product.id
    coupon.delete()
    messages.success(request, "Cupón eliminado.")
    return redirect('manage_coupons', product_id=product_id)