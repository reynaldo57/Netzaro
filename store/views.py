from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Profile, Comment, CommentResponse, Clase, Wishlist
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

    # Matrícula (crear)
    if request.method == 'POST' and 'comment_form' in request.POST:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.product = product
            if request.user.is_authenticated:
                comment.user = request.user
            comment.save()
            return redirect('product',pk=pk)
    else:
        form = CommentForm()

    # Respuesta a matrícula
    if request.method == 'POST' and 'respuesta_form' in request.POST:
        comment_id = request.POST.get('comment_id')
        comment_obj = get_object_or_404(Comment, id=comment_id)
        response_form = CommentResponseForm(request.POST)
        if response_form.is_valid():
            response = response_form.save(commit=False)
            response.comment = comment_obj
            response.save()
            return redirect('product',pk=pk)
    else:
        response_form = CommentResponseForm()

    return render(request, 'product.html', {
        'product': product,
        'form': form,
        'comments': comments,
        'response_form': response_form,
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
    formClase = AddClaseForm(initial={'productClase': productClase})

    if request.method == "POST":
        formClase = AddClaseForm(request.POST, request.FILES)
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
    }
    return render(request, 'add_clase.html', context)




def product_detail_view(request, id):
    product = get_object_or_404(Product, id=id)

    clases_basico = Clase.objects.filter(productClase=product, nivel="Basico")
    clases_intermedio = Clase.objects.filter(productClase=product, nivel="Intermedio")
    clases_avanzado = Clase.objects.filter(productClase=product, nivel="Avanzado")

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
    context = {
        "product": product,
        "clases_basico": clases_basico,
        "clases_intermedio": clases_intermedio,
        "clases_avanzado": clases_avanzado,
        "clases_pagadas": clases_pagadas,
        "recommended_products": recommended_products,
        "in_wishlist": in_wishlist,
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