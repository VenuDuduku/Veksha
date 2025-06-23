import os
import logging  # <-- Add this

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import bcrypt
from datetime import datetime
import json
import locale
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.debug = True

# Enable debug-level logging
logging.basicConfig(level=logging.DEBUG)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ecommerce.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images/products'


# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore

# Custom Jinja2 filter for Indian Rupee formatting
@app.template_filter('inr')
def format_inr(amount):
    """Format amount as Indian Rupees"""
    try:
        # Format with commas for thousands and 2 decimal places
        formatted = "{:,.2f}".format(float(amount))
        return f"₹{formatted}"
    except:
        return f"₹{amount}"

# Custom Jinja2 filter for newline to break conversion
@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to HTML line breaks"""
    if value:
        return value.replace('\n', '<br>')
    return value

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Profile relationship
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100))
    profile_picture = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(200))
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref='cart_items')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Shipping and payment information
    shipping_address = db.Column(db.Text)
    billing_address = db.Column(db.Text)
    payment_method = db.Column(db.String(50))
    payment_status = db.Column(db.String(20), default='pending')
    tracking_number = db.Column(db.String(100))
    
    user = db.relationship('User', backref='orders')
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database and create sample data
def initialize_database():
    """Initialize database tables and create sample data if needed"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if not exists
        admin_username = os.environ.get('ADMIN_USERNAME', 'Veksha')
        admin_email = os.environ.get('ADMIN_EMAIL', 'veksha@admin.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'Lucky1326')
        
        admin = User.query.filter_by(username=admin_username).first()
        if not admin:
            admin = User()
            admin.username = admin_username
            admin.email = admin_email
            admin.is_admin = True
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created: username='{admin_username}', password='{admin_password}'")
        
        # Add sample products if none exist
        if Product.query.count() == 0:
            def create_product(name, description, price, stock, category, image_url):
                product = Product()
                product.name = name
                product.description = description
                product.price = price
                product.stock = stock
                product.category = category
                product.image_url = image_url
                return product
            
            sample_products = [
                # Electronics Category (15 products)
                create_product('Laptop', 'High-performance laptop with Intel i7 processor, 16GB RAM, and 512GB SSD. Perfect for work and gaming.', 74999.00, 10, 'Electronics', 'images/products/laptop.jpg'),
                create_product('Smartphone', 'Latest smartphone model with 128GB storage, 6.1-inch display, and advanced camera system.', 52499.00, 15, 'Electronics', 'images/products/smartphone.jpg'),
                create_product('Headphones', 'Wireless noise-canceling headphones with premium sound quality and 30-hour battery life.', 14999.00, 20, 'Electronics', 'images/products/headphones.jpg'),
                create_product('Tablet', '10.1-inch tablet with 64GB storage, perfect for entertainment and productivity.', 22499.00, 12, 'Electronics', 'images/products/tablet.jpg'),
                create_product('Smartwatch', 'Fitness tracking smartwatch with heart rate monitor and GPS.', 8999.00, 25, 'Electronics', 'images/products/smartwatch.jpg'),
                create_product('Wireless Earbuds', 'True wireless earbuds with active noise cancellation and 24-hour battery.', 12499.00, 30, 'Electronics', 'images/products/earbuds.jpg'),
                create_product('Gaming Console', 'Next-gen gaming console with 1TB storage and wireless controller.', 44999.00, 8, 'Electronics', 'images/products/gaming-console.jpg'),
                create_product('Bluetooth Speaker', 'Portable Bluetooth speaker with 360-degree sound and waterproof design.', 3499.00, 40, 'Electronics', 'images/products/bluetooth-speaker.jpg'),
                create_product('Power Bank', '20000mAh power bank with fast charging and multiple USB ports.', 2499.00, 50, 'Electronics', 'images/products/power-bank.jpg'),
                create_product('Webcam', 'HD webcam with built-in microphone for video calls and streaming.', 4499.00, 35, 'Electronics', 'images/products/webcam.jpg'),
                create_product('External Hard Drive', '2TB external hard drive with USB 3.0 for fast data transfer.', 5999.00, 20, 'Electronics', 'images/products/hard-drive.jpg'),
                create_product('Mechanical Keyboard', 'RGB mechanical keyboard with customizable switches and wrist rest.', 8999.00, 15, 'Electronics', 'images/products/keyboard.jpg'),
                create_product('Gaming Mouse', 'High-precision gaming mouse with adjustable DPI and programmable buttons.', 3999.00, 25, 'Electronics', 'images/products/gaming-mouse.jpg'),
                create_product('Monitor', '27-inch 4K monitor with HDR support and adjustable stand.', 29999.00, 10, 'Electronics', 'images/products/monitor.jpg'),
                create_product('Printer', 'All-in-one wireless printer with scanner and copier functionality.', 12499.00, 12, 'Electronics', 'images/products/printer.jpg'),
                
                # Clothing Category (12 products)
                create_product('T-Shirt', 'Comfortable cotton t-shirt available in multiple colors and sizes. Perfect for everyday wear.', 2249.00, 50, 'Clothing', 'images/products/tshirt.jpg'),
                create_product('Jeans', 'High-quality denim jeans with perfect fit and durable construction. Available in various styles.', 5999.00, 30, 'Clothing', 'images/products/jeans.jpg'),
                create_product('Formal Shirt', 'Premium cotton formal shirt suitable for office and business meetings.', 3499.00, 25, 'Clothing', 'images/products/formal-shirt.jpg'),
                create_product('Dress', 'Elegant summer dress with floral pattern, perfect for casual and semi-formal occasions.', 4499.00, 20, 'Clothing', 'images/products/dress.jpg'),
                create_product('Sweater', 'Warm woolen sweater for cold weather, available in multiple colors.', 3999.00, 35, 'Clothing', 'images/products/sweater.jpg'),
                create_product('Jacket', 'Stylish leather jacket with comfortable fit and durable material.', 8999.00, 15, 'Clothing', 'images/products/jacket.jpg'),
                create_product('Saree', 'Traditional silk saree with beautiful embroidery and elegant design.', 12499.00, 10, 'Clothing', 'images/products/saree.jpg'),
                create_product('Kurta', 'Traditional Indian kurta with modern design, perfect for festivals and celebrations.', 2999.00, 30, 'Clothing', 'images/products/kurta.jpg'),
                create_product('Suit', 'Professional business suit with matching trousers and jacket.', 15999.00, 12, 'Clothing', 'images/products/suit.jpg'),
                create_product('Sneakers', 'Comfortable sneakers with cushioned sole and breathable material.', 4499.00, 40, 'Clothing', 'images/products/sneakers.jpg'),
                create_product('Heels', 'Elegant high heels suitable for formal occasions and parties.', 3499.00, 25, 'Clothing', 'images/products/heels.jpg'),
                create_product('Handbag', 'Stylish leather handbag with multiple compartments and adjustable strap.', 5999.00, 20, 'Clothing', 'images/products/handbag.jpg'),
                
                # Sports Category (8 products)
                create_product('Running Shoes', 'Lightweight running shoes with superior comfort and excellent traction for all terrains.', 6749.00, 25, 'Sports', 'images/products/shoes.jpg'),
                create_product('Yoga Mat', 'Non-slip yoga mat with comfortable cushioning for all types of exercises.', 1499.00, 60, 'Sports', 'images/products/yoga-mat.jpg'),
                create_product('Dumbbells Set', 'Adjustable dumbbells set with storage rack for home workouts.', 8999.00, 15, 'Sports', 'images/products/dumbbells.jpg'),
                create_product('Bicycle', 'Mountain bike with 21-speed gear system and durable frame.', 22499.00, 8, 'Sports', 'images/products/bicycle.jpg'),
                create_product('Tennis Racket', 'Professional tennis racket with comfortable grip and optimal balance.', 4499.00, 20, 'Sports', 'images/products/tennis-racket.jpg'),
                create_product('Cricket Bat', 'Premium willow cricket bat with perfect weight and balance.', 8999.00, 12, 'Sports', 'images/products/cricket-bat.jpg'),
                create_product('Football', 'Official size football with durable outer cover and perfect bounce.', 2499.00, 30, 'Sports', 'images/products/football.jpg'),
                create_product('Gym Bag', 'Large gym bag with multiple compartments and comfortable shoulder straps.', 1999.00, 40, 'Sports', 'images/products/gym-bag.jpg'),
                
                # Home & Garden Category (10 products)
                create_product('Coffee Maker', 'Programmable coffee maker with 12-cup capacity and auto-shutoff feature for convenience.', 3749.00, 12, 'Home & Garden', 'images/products/coffee-maker.jpg'),
                create_product('Microwave Oven', '20L microwave oven with multiple cooking modes and child lock feature.', 5999.00, 18, 'Home & Garden', 'images/products/microwave.jpg'),
                create_product('Blender', 'High-speed blender with multiple attachments for smoothies and food processing.', 2999.00, 25, 'Home & Garden', 'images/products/blender.jpg'),
                create_product('Toaster', '2-slice toaster with adjustable browning control and removable crumb tray.', 1999.00, 30, 'Home & Garden', 'images/products/toaster.jpg'),
                create_product('Bed Sheet Set', 'Cotton bed sheet set with pillow covers, available in multiple colors.', 2499.00, 35, 'Home & Garden', 'images/products/bed-sheets.jpg'),
                create_product('Pillow', 'Memory foam pillow with ergonomic design for better sleep quality.', 1499.00, 50, 'Home & Garden', 'images/products/pillow.jpg'),
                create_product('Table Lamp', 'Modern LED table lamp with adjustable brightness and touch control.', 1999.00, 40, 'Home & Garden', 'images/products/table-lamp.jpg'),
                create_product('Plant Pot', 'Decorative ceramic plant pot with drainage hole, perfect for indoor plants.', 899.00, 60, 'Home & Garden', 'images/products/plant-pot.jpg'),
                create_product('Garden Tools Set', 'Complete garden tools set with storage bag for all gardening needs.', 3499.00, 20, 'Home & Garden', 'images/products/garden-tools.jpg'),
                create_product('Vacuum Cleaner', 'Cordless vacuum cleaner with HEPA filter and multiple attachments.', 12499.00, 15, 'Home & Garden', 'images/products/vacuum-cleaner.jpg'),
                
                # Other Category (5 products)
                create_product('Backpack', 'Durable backpack with multiple compartments, laptop sleeve, and water-resistant material.', 4499.00, 18, 'Other', 'images/products/backpack.jpg'),
                create_product('Umbrella', 'Automatic umbrella with wind-resistant design and comfortable handle.', 899.00, 45, 'Other', 'images/products/umbrella.jpg'),
                create_product('Water Bottle', 'Insulated water bottle that keeps drinks cold for 24 hours.', 1499.00, 55, 'Other', 'images/products/water-bottle.jpg'),
                create_product('Sunglasses', 'Polarized sunglasses with UV protection and comfortable fit.', 2999.00, 30, 'Other', 'images/products/sunglasses.jpg'),
                create_product('Wallet', 'Genuine leather wallet with multiple card slots and coin compartment.', 1999.00, 40, 'Other', 'images/products/wallet.jpg'),
            ]
            db.session.add_all(sample_products)
            db.session.commit()
            print("50 sample products added!")

# Initialize database on app startup
initialize_database()

# Routes
@app.route('/')
def index():
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    
    products = Product.query
    
    if search_query:
        products = products.filter(
            db.or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.description.ilike(f'%{search_query}%'),
                Product.category.ilike(f'%{search_query}%')
            )
        )
    
    if category_filter:
        products = products.filter(Product.category == category_filter)
    
    products = products.all()
    
    # Get unique categories for filter dropdown
    categories = db.session.query(Product.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('index.html', products=products, search_query=search_query, 
                         category_filter=category_filter, categories=categories)

@app.route('/search')
def search():
    search_query = request.args.get('q', '')
    category_filter = request.args.get('category', '')
    
    products = Product.query
    
    if search_query:
        products = products.filter(
            db.or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.description.ilike(f'%{search_query}%'),
                Product.category.ilike(f'%{search_query}%')
            )
        )
    
    if category_filter:
        products = products.filter(Product.category == category_filter)
    
    products = products.all()
    
    # Get unique categories for filter dropdown
    categories = db.session.query(Product.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('search_results.html', products=products, search_query=search_query, 
                         category_filter=category_filter, categories=categories)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!')
            return redirect(url_for('register'))
        
        user = User()
        user.username = username
        user.email = email
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Get or create user profile
        profile = current_user.profile
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.session.add(profile)
        
        # Update profile information
        profile.first_name = request.form.get('first_name', '')
        profile.last_name = request.form.get('last_name', '')
        profile.phone = request.form.get('phone', '')
        profile.gender = request.form.get('gender', '')
        
        # Handle date of birth
        dob_str = request.form.get('date_of_birth', '')
        if dob_str:
            try:
                profile.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Update address information
        profile.address_line1 = request.form.get('address_line1', '')
        profile.address_line2 = request.form.get('address_line2', '')
        profile.city = request.form.get('city', '')
        profile.state = request.form.get('state', '')
        profile.postal_code = request.form.get('postal_code', '')
        profile.country = request.form.get('country', '')
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Save to static/images/profiles directory
                profile_dir = 'static/images/profiles'
                os.makedirs(profile_dir, exist_ok=True)
                file.save(os.path.join(profile_dir, filename))
                profile.profile_picture = f'images/profiles/{filename}'
        
        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html')

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    
    # Check if item already in cart
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Item added to cart!')
    return redirect(url_for('index'))

@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    
    if cart_item.user_id != current_user.id:
        flash('Unauthorized!')
        return redirect(url_for('cart'))
    
    action = request.form.get('action')
    
    if action == 'remove':
        db.session.delete(cart_item)
    elif action == 'update':
        quantity = int(request.form.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
        else:
            db.session.delete(cart_item)
    
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # Check if this is a "Buy Now" purchase (direct product purchase)
    product_id = request.args.get('product_id')
    quantity = request.args.get('quantity', 1, type=int)
    
    if product_id:
        # Buy Now functionality - direct purchase
        product = Product.query.get_or_404(int(product_id))
        
        if product.stock < quantity:
            flash(f'Only {product.stock} items available in stock!')
            return redirect(url_for('index'))
        
        total = product.price * quantity
        
        if request.method == 'POST':
            # Get form data
            shipping_name = request.form.get('shipping_name', '')
            shipping_phone = request.form.get('shipping_phone', '')
            shipping_address_line1 = request.form.get('shipping_address_line1', '')
            shipping_address_line2 = request.form.get('shipping_address_line2', '')
            shipping_city = request.form.get('shipping_city', '')
            shipping_state = request.form.get('shipping_state', '')
            shipping_postal_code = request.form.get('shipping_postal_code', '')
            shipping_country = request.form.get('shipping_country', '')
            
            # Build shipping address string
            shipping_address = f"{shipping_name}\n{shipping_phone}\n{shipping_address_line1}"
            if shipping_address_line2:
                shipping_address += f"\n{shipping_address_line2}"
            shipping_address += f"\n{shipping_city}, {shipping_state} {shipping_postal_code}\n{shipping_country}"
            
            # Handle billing address
            same_as_shipping = request.form.get('same_as_shipping') == 'on'
            if same_as_shipping:
                billing_address = shipping_address
            else:
                billing_name = request.form.get('billing_name', '')
                billing_phone = request.form.get('billing_phone', '')
                billing_address_line1 = request.form.get('billing_address_line1', '')
                billing_address_line2 = request.form.get('billing_address_line2', '')
                billing_city = request.form.get('billing_city', '')
                billing_state = request.form.get('billing_state', '')
                billing_postal_code = request.form.get('billing_postal_code', '')
                billing_country = request.form.get('billing_country', '')
                
                billing_address = f"{billing_name}\n{billing_phone}\n{billing_address_line1}"
                if billing_address_line2:
                    billing_address += f"\n{billing_address_line2}"
                billing_address += f"\n{billing_city}, {billing_state} {billing_postal_code}\n{billing_country}"
            
            payment_method = request.form.get('payment_method', 'Cash on Delivery')
            
            # Create order for direct purchase
            order = Order()
            order.user_id = current_user.id
            order.total_amount = total
            order.shipping_address = shipping_address
            order.billing_address = billing_address
            order.payment_method = payment_method
            db.session.add(order)
            db.session.flush()  # Get order ID
            
            # Create order item
            order_item = OrderItem()
            order_item.order_id = order.id
            order_item.product_id = product.id
            order_item.quantity = quantity
            order_item.price = product.price
            db.session.add(order_item)
            
            # Update product stock
            product.stock -= quantity
            
            db.session.commit()
            flash('Order placed successfully!')
            return redirect(url_for('order_confirmation', order_id=order.id))
        
        return render_template('checkout.html', 
                             cart_items=[], 
                             total=total, 
                             buy_now=True, 
                             product=product, 
                             quantity=quantity)
    
    # Regular cart checkout
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Your cart is empty!')
        return redirect(url_for('cart'))
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    if request.method == 'POST':
        # Get form data
        shipping_name = request.form.get('shipping_name', '')
        shipping_phone = request.form.get('shipping_phone', '')
        shipping_address_line1 = request.form.get('shipping_address_line1', '')
        shipping_address_line2 = request.form.get('shipping_address_line2', '')
        shipping_city = request.form.get('shipping_city', '')
        shipping_state = request.form.get('shipping_state', '')
        shipping_postal_code = request.form.get('shipping_postal_code', '')
        shipping_country = request.form.get('shipping_country', '')
        
        # Build shipping address string
        shipping_address = f"{shipping_name}\n{shipping_phone}\n{shipping_address_line1}"
        if shipping_address_line2:
            shipping_address += f"\n{shipping_address_line2}"
        shipping_address += f"\n{shipping_city}, {shipping_state} {shipping_postal_code}\n{shipping_country}"
        
        # Handle billing address
        same_as_shipping = request.form.get('same_as_shipping') == 'on'
        if same_as_shipping:
            billing_address = shipping_address
        else:
            billing_name = request.form.get('billing_name', '')
            billing_phone = request.form.get('billing_phone', '')
            billing_address_line1 = request.form.get('billing_address_line1', '')
            billing_address_line2 = request.form.get('billing_address_line2', '')
            billing_city = request.form.get('billing_city', '')
            billing_state = request.form.get('billing_state', '')
            billing_postal_code = request.form.get('billing_postal_code', '')
            billing_country = request.form.get('billing_country', '')
            
            billing_address = f"{billing_name}\n{billing_phone}\n{billing_address_line1}"
            if billing_address_line2:
                billing_address += f"\n{billing_address_line2}"
            billing_address += f"\n{billing_city}, {billing_state} {billing_postal_code}\n{billing_country}"
        
        payment_method = request.form.get('payment_method', 'Cash on Delivery')
        
        # Create order
        order = Order()
        order.user_id = current_user.id
        order.total_amount = total
        order.shipping_address = shipping_address
        order.billing_address = billing_address
        order.payment_method = payment_method
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem()
            order_item.order_id = order.id
            order_item.product_id = cart_item.product_id
            order_item.quantity = cart_item.quantity
            order_item.price = cart_item.product.price
            db.session.add(order_item)
            
            # Update product stock
            cart_item.product.stock -= cart_item.quantity
        
        # Clear cart
        for cart_item in cart_items:
            db.session.delete(cart_item)
        
        db.session.commit()
        flash('Order placed successfully!')
        return redirect(url_for('order_confirmation', order_id=order.id))
    
    return render_template('checkout.html', cart_items=cart_items, total=total, buy_now=False)

@app.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized!')
        return redirect(url_for('index'))
    return render_template('order_confirmation.html', order=order)

@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Check if user owns this order
    if order.user_id != current_user.id:
        flash('Unauthorized!')
        return redirect(url_for('orders'))
    
    # Check if order can be cancelled (only pending orders)
    if order.status != 'pending':
        flash('Only pending orders can be cancelled!')
        return redirect(url_for('orders'))
    
    # Restore product stock
    for item in order.items:
        item.product.stock += item.quantity
    
    # Update order status to cancelled
    order.status = 'cancelled'
    
    db.session.commit()
    flash('Order cancelled successfully!')
    return redirect(url_for('orders'))

# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied!')
        return redirect(url_for('index'))
    
    try:
        products = Product.query.all()
        orders = Order.query.order_by(Order.created_at.desc()).all()
        total_orders = len(orders)
        total_revenue = sum(order.total_amount for order in orders if order.status == 'completed')
        
        # Debug information
        print(f"Admin Dashboard - Products: {len(products)}, Orders: {total_orders}, Revenue: {total_revenue}")
        print(f"Current user: {current_user.username}, Is admin: {current_user.is_admin}")
        
        return render_template('admin/dashboard.html', 
                             products=products, 
                             orders=orders, 
                             total_orders=total_orders,
                             total_revenue=total_revenue)
    except Exception as e:
        print(f"Error in admin dashboard: {e}")
        flash(f'Error loading dashboard: {e}')
        return redirect(url_for('index'))

@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_admin:
        flash('Access denied!')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        category = request.form['category']
        
        # Handle image upload
        image_url = ''
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = f'images/products/{filename}'
        
        product = Product()
        product.name = name
        product.description = description
        product.price = price
        product.stock = stock
        product.category = category
        product.image_url = image_url
        
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_product.html')

@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.is_admin:
        flash('Access denied!')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        product.category = request.form['category']
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.image_url = f'images/products/{filename}'
        
        db.session.commit()
        flash('Product updated successfully!')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/delete_product/<int:product_id>')
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        flash('Access denied!')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('Access denied!')
        return redirect(url_for('index'))
    
    try:
        orders = Order.query.order_by(Order.created_at.desc()).all()
        print(f"Admin Orders - Total orders: {len(orders)}")
        for order in orders:
            print(f"Order #{order.id}: {order.user.username}, Amount: {order.total_amount}, Status: {order.status}")
        
        return render_template('admin/orders.html', orders=orders)
    except Exception as e:
        print(f"Error in admin orders: {e}")
        flash(f'Error loading orders: {e}')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        flash('Access denied!')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    new_status = request.form['status']
    old_status = order.status
    
    # Handle stock management based on status changes
    if new_status == 'cancelled' and old_status != 'cancelled':
        # Restore stock when cancelling
        for item in order.items:
            item.product.stock += item.quantity
        flash('Order cancelled and stock restored!')
    elif old_status == 'cancelled' and new_status != 'cancelled':
        # Deduct stock when uncancelling (if it was previously cancelled)
        for item in order.items:
            if item.product.stock >= item.quantity:
                item.product.stock -= item.quantity
            else:
                flash(f'Insufficient stock for {item.product.name}!')
                return redirect(url_for('admin_orders'))
        flash('Order status updated and stock adjusted!')
    else:
        flash('Order status updated!')
    
    order.status = new_status
    db.session.commit()
    return redirect(url_for('admin_orders'))

# API routes for real-time updates
@app.route('/api/cart_count')
@login_required
def cart_count():
    count = CartItem.query.filter_by(user_id=current_user.id).count()
    return jsonify({'count': count})

@app.route('/api/cart_total')
@login_required
def cart_total():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return jsonify({'total': total})

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Get related products from the same category
    related_products = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id
    ).limit(4).all()
    
    return render_template('product_detail.html', product=product, related_products=related_products)

if __name__ == '__main__':
    app.run(debug=True) 