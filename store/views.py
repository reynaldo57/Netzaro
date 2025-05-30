from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Profile, Comment, CommentResponse, Clase
from cart.cart import Cart
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm, UpdateProfileForm, CommentForm, CommentResponseForm, AddProductForm, AddClaseForm
from payment.forms import ShippingForm
from payment.models import ShippingAddress
from django import forms
from django.db.models import Q
import json
from django.contrib.auth.decorators import login_required



# Create your views here.
def search(request):
    if request.method == "POST":
        searched = request.POST['searched']
        searched = Product.objects.filter(Q(name__icontains=searched) | Q(description__icontains=searched))
        if not searched:
            messages.success(request, "That Product does not exist")
            return render(request, "search.html", {})
        else:
            return render(request, "search.html", {'searched': searched})
    else:
        return render(request, "search.html", {})
    
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
    products = Product.objects.all()
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

    context = {
        "product": product,
        "clases_basico": clases_basico,
        "clases_intermedio": clases_intermedio,
        "clases_avanzado": clases_avanzado,
    }
    return render(request, 'product_detail.html', context)

