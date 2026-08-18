from store.models import Product, Profile
class Cart():
    def __init__(self, request):
        self.session = request.session
        self.request = request

        cart = self.session.get('session_key')

        if 'session_key' not in request.session:
            cart = self.session['session_key'] = {}

        self.cart = cart

    def db_add(self, product, quantity):
        product_id = str(product)
        product_qty = str(quantity)

        if product_id in self.cart:
            pass
        else:
            #self.cart[product_id] = {'price': str(product.price)}
            self.cart[product_id] = int(product_qty)

        self.session.modified = True

        if self.request.user.is_authenticated:
            current_user = Profile.objects.filter(user__id=self.request.user.id)

            carty = str(self.cart)
            carty = carty.replace("\'","\"")
            current_user.update(old_cart=str(carty))

    def add(self, product, quantity):
        product_id = str(product.id)
        product_qty = str(quantity)

        if product_id in self.cart:
            pass
        else:
            #self.cart[product_id] = {'price': str(product.price)}
            self.cart[product_id] = int(product_qty)

        self.session.modified = True

        if self.request.user.is_authenticated:
            current_user = Profile.objects.filter(user__id=self.request.user.id)

            carty = str(self.cart)
            carty = carty.replace("\'","\"")
            current_user.update(old_cart=str(carty))

    def cart_total(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        quantities = self.cart
        total = 0
        coupon = self.get_coupon()
        for key, value in quantities.items():
            key = int(key)
            for product in products:
                if product.id == key:
                    if product.is_sale:
                        price = product.sale_price
                    else:
                        price = product.price
                    if coupon and coupon.product_id == product.id:
                        price = coupon.precio_con_descuento(price)
                    total = total + (price * value)
        return total

    def apply_coupon(self, code):
        from store.models import Coupon
        code = (code or '').strip()
        if not code:
            return None
        coupon = Coupon.objects.filter(code__iexact=code).first()
        if not coupon or not coupon.es_valido():
            return None
        self.session['coupon_code'] = coupon.code
        self.session.modified = True
        return coupon

    def get_coupon(self):
        from store.models import Coupon
        code = self.session.get('coupon_code')
        if not code:
            return None
        coupon = Coupon.objects.filter(code__iexact=code).first()
        if coupon and coupon.es_valido() and str(coupon.product_id) in self.cart:
            return coupon
        return None

    def remove_coupon(self):
        self.session.pop('coupon_code', None)
        self.session.modified = True

    def __len__(self):
        return len(self.cart)
    
    def get_prods(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        return products
    
    def get_quants(self):
        quantities = self.cart
        return quantities
    
    def update(self, product, quantity):
        product_id = str(product)
        product_qty = int(quantity)

        ourcart = self.cart
        ourcart[product_id] = product_qty

        self.session.modified = True

        

        if self.request.user.is_authenticated:
            current_user = Profile.objects.filter(user__id=self.request.user.id)

            carty = str(self.cart)
            carty = carty.replace("\'","\"")
            current_user.update(old_cart=str(carty))

        thing =  self.cart    
        return thing
    
    def delete(self, product):
        product_id = str(product)
        if product_id in self.cart:
            del self.cart[product_id]

        self.session.modified = True

        if self.request.user.is_authenticated:
            current_user = Profile.objects.filter(user__id=self.request.user.id)

            carty = str(self.cart)
            carty = carty.replace("\'","\"")
            current_user.update(old_cart=str(carty))