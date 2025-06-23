# 🛍️ Veksha E-commerce Platform

A modern, feature-rich e-commerce web application built with Flask, featuring user authentication, product management, shopping cart functionality, and admin dashboard.

## ✨ Features

### 🛒 Customer Features
- **User Registration & Authentication** - Secure login/logout system
- **Product Browsing** - Browse products by category with search functionality
- **Shopping Cart** - Add/remove items, update quantities
- **Buy Now** - Direct product purchase without cart
- **Checkout System** - Complete with shipping/billing addresses
- **Order Management** - View order history and cancel orders
- **User Profiles** - Edit personal information and upload profile pictures
- **Product Details** - Detailed product pages with related products

### 👨‍💼 Admin Features
- **Admin Dashboard** - Overview of products, orders, and revenue
- **Product Management** - Add, edit, and delete products
- **Order Management** - View and update order statuses
- **Inventory Management** - Automatic stock updates

### 🎨 Design Features
- **Responsive Design** - Mobile-friendly interface
- **Modern UI** - Clean and intuitive user interface
- **Indian Rupee Formatting** - Proper currency display
- **Image Upload** - Product and profile picture management

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/veksha-ecommerce.git
   cd veksha-ecommerce
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env with your own values
   # IMPORTANT: Change the SECRET_KEY and admin credentials!
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your browser and go to `http://127.0.0.1:5000`
   - Admin login: Username: `Veksha`, Password: `Lucky1326`

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=sqlite:///ecommerce.db

# Admin Credentials (Change these!)
ADMIN_USERNAME=Veksha
ADMIN_EMAIL=veksha@admin.com
ADMIN_PASSWORD=Lucky1326

# Flask Settings
FLASK_ENV=development
FLASK_DEBUG=True

# Upload Settings
UPLOAD_FOLDER=static/images/products
MAX_CONTENT_LENGTH=16777216
```

### Database Setup

The application automatically creates the database and sample data on first run. The database file (`ecommerce.db`) will be created in the `instance/` directory.

## 📁 Project Structure

```
veksha-ecommerce/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── env.example           # Environment variables template
├── README.md             # This file
├── static/               # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
│       ├── products/     # Product images
│       └── profiles/     # User profile pictures
├── templates/            # HTML templates
│   ├── admin/           # Admin templates
│   └── ...              # Other templates
└── instance/            # Instance-specific files (database)
    └── ecommerce.db     # SQLite database (not in git)
```

## 🔒 Security Features

- **Password Hashing** - Uses bcrypt for secure password storage
- **Environment Variables** - Sensitive data stored in .env file
- **SQL Injection Protection** - Uses SQLAlchemy ORM
- **CSRF Protection** - Built-in Flask protection
- **Secure File Uploads** - Validates and secures uploaded files

## 🛡️ Security Best Practices

### For Production Deployment

1. **Change Default Credentials**
   - Update admin username and password in `.env`
   - Use a strong, unique SECRET_KEY

2. **Database Security**
   - Use PostgreSQL or MySQL instead of SQLite
   - Set up proper database user permissions

3. **File Upload Security**
   - Implement file type validation
   - Set up cloud storage (AWS S3, etc.)

4. **HTTPS**
   - Use SSL/TLS certificates
   - Configure secure headers

5. **Environment**
   - Set `FLASK_ENV=production`
   - Set `FLASK_DEBUG=False`

## 📝 API Endpoints

### Public Routes
- `GET /` - Homepage with products
- `GET /search` - Product search
- `GET /product/<id>` - Product details
- `GET /register` - User registration
- `GET /login` - User login

### Protected Routes (Login Required)
- `GET /profile` - User profile
- `GET /cart` - Shopping cart
- `GET /checkout` - Checkout page
- `GET /orders` - Order history
- `POST /add_to_cart/<id>` - Add to cart

### Admin Routes
- `GET /admin` - Admin dashboard
- `GET /admin/orders` - Order management
- `GET /admin/add_product` - Add product
- `POST /admin/edit_product/<id>` - Edit product

## 🛠️ Development

### Adding New Features

1. **Database Models** - Add new models in `app.py`
2. **Routes** - Add new routes in `app.py`
3. **Templates** - Create HTML templates in `templates/`
4. **Static Files** - Add CSS/JS in `static/`

### Database Migrations

For production, consider using Flask-Migrate for database migrations:

```bash
pip install Flask-Migrate
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues:

1. Check the [Issues](https://github.com/yourusername/veksha-ecommerce/issues) page
2. Create a new issue with detailed information
3. Include error messages and steps to reproduce

## 🙏 Acknowledgments

- Flask framework and community
- Bootstrap for responsive design
- Font Awesome for icons
- SQLAlchemy for database ORM

---

**Note**: This is a development project. For production use, ensure proper security measures are implemented. 

## 🤔 Troubleshooting

### Error: "no such table"

If you encounter the error "no such table", it means that the tables in your database do not exist. This can happen if the database has not been initialized or migrated before the app starts.

#### Solution:

1. **Ensure Database Initialization on Render**

   On your local machine, the database is created automatically on first run. On Render, you need to make sure the same thing happens.

   - **Option A: Auto-create on App Start**
     If your `app.py` already creates the database and tables if they don't exist, make sure this code runs on Render as well.  
     Look for code like:
     ```python
     from app import db
     db.create_all()
     ```
     If not present, you should add logic to create tables if they don't exist.

   - **Option B: Use a Startup Command**
     You can add a command in your `render.yaml` or as a Render "Build Command" to initialize the database before starting the app.

     For example, if you use Flask-Migrate:
     ```bash
     flask db upgrade
     ```
     Or, for basic SQLAlchemy:
     ```bash
     python -c "from app import db; db.create_all()"
     ```

2. **Check Your Database Path**
   - If you use SQLite, make sure the path is writable and accessible on Render.
   - The default path in your `.env` is `sqlite:///ecommerce.db`, but your code may expect it in the `instance/` folder.
   - On Render, you may need to set `DATABASE_URL=sqlite:///instance/ecommerce.db` and ensure the `instance/` directory exists and is writable.

3. **Review Environment Variables**
   - Make sure all required environment variables are set in Render's dashboard (especially `DATABASE_URL`).

#### Next Steps

1. **Check your Render logs for the full error message** (especially the lines before/after the snippet you posted).
2. **Confirm if the database file is being created** in the right place.
3. **Ensure your app creates tables on first run** (or use a migration tool).

#### If you share your `app.py` database setup code or the full error log, I can give you a more specific fix!

Would you like instructions on how to add auto-creation of tables, or help with configuring your `render.yaml`? 