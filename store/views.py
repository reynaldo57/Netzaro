from django.shortcuts import render, redirect
from .models import Product, Category, Profile
from cart.cart import Cart
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm, UpdateProfileForm
from payment.forms import ShippingForm
from payment.models import ShippingAddress
from django import forms
from django.db.models import Q
import json


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

def product(request,pk):
    product = Product.objects.get(id=pk)
    return render(request, 'product.html', {'product':product})

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