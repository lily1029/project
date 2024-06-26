from django.shortcuts import render, redirect
from allauth.account.signals import user_logged_in
from django.dispatch.dispatcher import receiver
from django.forms.models import model_to_dict
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DeleteView
from django.contrib import messages

# Login
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm

# Authorization
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin


import uuid
import boto3
import os
# ---confirm with Dean this model is done then migrate
from .models import Furniture_Item, Photo, Cart

# furniture = [
# 	{'name':'Blue chair', 'description': 'Blue LazyBoy', 'price':'500.00', 'category':'chair'},
# 	{'name':'Dining table', 'description': 'Oak Dining Table', 'price':'1000.00', 'category':'table'},
#  	{'name':'Canopy Bed', 'description': 'Black metal canopy bed', 'price':'250.00', 'category':'bed'},
# 	{'name':'Sectional', 'description': 'Leather Sectional', 'price':'1500,00', 'category':'sofa'}
# ]


@receiver(user_logged_in, dispatch_uid="unique")
def user_logged_in_(request, user, **kwargs):
	print(request.user)


def home(request):
	# furniture = furniture.objects.all()

	return render(request, 'home.html')


def signup(request):
	error_message = ''
	if request.method == "POST":
		form = UserCreationForm(request.POST)
		if form.is_valid():
			# save the user to the database
			user = form.save()  # this adds user to the table in psql
			# login our user
			login(request, user)
			return redirect('index')  # index is the name of the url path
		else:
			error_message = "Invalid signup - try again"
	form = UserCreationForm()
	return render(request, 'registration/signup.html', {
		'error_message': error_message,
		'form': form
	})

# ----WILL NEED TO ADD FILTER METHOD HERE----#


def furniture_index(request):
	category = request.GET.get('category')
	if category:
		furniture = Furniture_Item.objects.filter(category=category)
		return render(request, 'furniture/index.html', {
			'furniture': furniture
		})
	else:
		furniture = Furniture_Item.objects.all()
		return render(request, 'furniture/index.html', {
			'furniture': furniture
	})


def furniture_detail(request, furniture_item_id):
	furniture = Furniture_Item.objects.get(id=furniture_item_id)
	return render(request, 'furniture/detail.html', {
		'furniture_item': furniture,
	})

 ## ---create furniture----####

 # AAU (ADMIN ONLY) I want to create new furniture item


class Furniture_Item_Create(CreateView):
	model = Furniture_Item
	fields = ['name', 'description', 'price', 'category']

	# def form_valid(self, form):
	# 	#uncomment this when signup is fully working
	# 	form.instance.user = self.request.user
	# 	return super().form_valid(form)


class Furniture_Item_Delete(DeleteView):
	model = Furniture_Item
	# define the success_url here because the def get_absolute_url in the models.property
	# redirects to a detail page which doesn't make sense since we deleted it
	success_url = '/furniture'  # redirect to cats_index path


def add_photo(request, furniture_item_id):
	# photo-file will be the "name" attribute on the <input type="file">
	photo_file = request.FILES.get('photo-file', None)
	if photo_file:
		s3 = boto3.client('s3')
		# need a unique "key" for S3 / needs image file extension too
		key = "furniture_gallery/" + \
		    uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
		# just in case something goes wrong
		try:
			bucket = os.environ['S3_BUCKET']
			s3.upload_fileobj(photo_file, bucket, key)
			# build the full url string
			url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
			# we can assign to furniture_id or cat (if you have a furniture object)
			Photo.objects.create(url=url, furniture_item_id=furniture_item_id)
		except Exception as e:
			print('An error occurred uploading file to S3')
			print(e)
	return redirect('detail', furniture_item_id=furniture_item_id)


class CartCreate(CreateView):
	model = Cart
	fields = '__all__'


class CartUpdate(UpdateView):
	model = Cart
	fields = '__all__'

# class CartList(ListView):
# 	model = Cart

# 	def get_context_data(self, **kwargs):
# 		context = super().get_context_data(**kwargs)
# 		cart_list = context['cart_list']
# 		for cart in cart_list:
# 			print(model_to_dict(cart))
# 		return context


def cart_list(request):
	cart = Cart.objects.get(user=request.user)
	print(cart)
	total_price = sum([item.price * item.quantity for item in cart.furniture_item.all()])
	return render(request, 'main_app/cart_list.html', {'cart': cart, 'total_price': total_price})

# def cart_list(request):
# 	cart = Furniture_Item.objects.filter() 
# 	total_price = sum(item.price * item for item in cart)
# 	# total_price = sum(cart_items.furniture_item.price * cart_items.furniture_item.quantity for cart in cart_items)
# 	return render(request, 'main_app/cart_list.html', {'total_price': total_price})


def disassoc_item(request, cart_id, furniture_item_id):
	cart = Cart.objects.get(id=cart_id)
	cart.furniture_item.remove(furniture_item_id)
	return redirect('cart_list')





# we want to"
# 1 find cart by the user similar to cart = Cart.objects.get(id=cart_id)
#3 if it finds the object:
#4 if we found it, now we need to check to see if the item is in the cart
#5 if item is in the cart then we want to increase the quantity
#6 if the item is not in the cart, we add the item to the cart make quanity +1
#7 then we respond to redirect back to the detail page
def assoc_item(request, furniture_item_id):
	cart = Cart.objects.get(user=request.user)
	print(cart.__dict__, "This is request for assoc_item")
	print(cart, "this is cart")
	try:
		item = cart.furniture_item.get(id=furniture_item_id)
		item.quantity += 1
		item.save()
		print(request, "Item added to your cart")
	except Furniture_Item.DoesNotExist:
			item = cart.furniture_item.add(furniture_item_id)
	# if cart has something call .save
	# else:
	# 	Cart.objects.create(user=request.user, furniture_item=furniture_item_id)
 	# cart = Cart.objects.get(id=cart_id)
	# cart.furniture.add(furniture_item_id)# adding a row to our through table the one with 2 foriegn keys in sql
	return redirect('cart_list')
