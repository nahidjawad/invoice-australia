# Database Migration & Company Feature Setup

This guide explains how to set up database migrations using Flask-Migrate and enable the company feature (many-to-many relationship between users and companies) in your Flask project.

---

## 1. Flask-Migrate Setup

### Install Flask-Migrate
```bash
pip install Flask-Migrate
```

### Register Flask-Migrate in Your App
- In `extensions.py`, ensure you have:
  ```python
  from flask_sqlalchemy import SQLAlchemy
  db = SQLAlchemy()
  ```
- In `app.py`, after initializing extensions:
  ```python
  from flask_migrate import Migrate
  from extensions import db

  def create_app(config_name=None):
      app = Flask(__name__)
      # ... config ...
      init_extensions(app)  # This calls db.init_app(app)
      migrate = Migrate(app, db)  # Register Flask-Migrate
      # ... register blueprints ...
      return app
  ```
- **Do NOT call `db.create_all()` or `db.init_app(app)` more than once.**

---

## 2. Models: User & Company (Many-to-Many)

- In `models.py`:
  ```python
  from extensions import db
  from datetime import datetime

  user_company = db.Table('user_company',
      db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
      db.Column('company_id', db.Integer, db.ForeignKey('companies.id'), primary_key=True)
  )

  class User(db.Model):
      __tablename__ = 'users'
      id = db.Column(db.Integer, primary_key=True)
      # ... other fields ...
      companies = db.relationship('Company', secondary=user_company, back_populates='users')

  class Company(db.Model):
      __tablename__ = 'companies'
      id = db.Column(db.Integer, primary_key=True)
      company_name = db.Column(db.String(120), nullable=False)
      abn = db.Column(db.String(20), nullable=True)
      address = db.Column(db.String(255), nullable=True)
      phone = db.Column(db.String(20), nullable=True)
      email = db.Column(db.String(120), nullable=True)
      payment_details = db.Column(db.Text, nullable=True)
      logo_path = db.Column(db.String(255), nullable=True)
      created_at = db.Column(db.DateTime, default=datetime.utcnow)
      updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
      users = db.relationship('User', secondary=user_company, back_populates='companies')
  ```

---

## 3. Migration Workflow

### Initializing Migrations (First Time Only)
```bash
export FLASK_APP=app.py  # or your main app file
flask db init
```

### Creating a Migration
```bash
flask db migrate -m "Describe your migration here"
```

### Applying the Migration
```bash
flask db upgrade
```

---

## 4. Company Feature: Creating a Company

- Use a blueprint (e.g., `company.py`) to handle company creation and association with the current user.
- Example route:
  ```python
  @company_bp.route('/company/create', methods=['GET', 'POST'])
  def create_company():
      if 'user' not in session:
          return redirect(url_for('auth.login'))
      if request.method == 'POST':
          # ... get form data ...
          company = Company(...)
          db.session.add(company)
          user = User.query.get(session['user']['id'])
          company.users.append(user)
          db.session.commit()
          flash('Company created and linked to your account!', 'success')
          return redirect(url_for('company.create_company'))
      return render_template('create_company.html')
  ```

---

## 5. Best Practices

- **Use a single `db = SQLAlchemy()` instance** (in `extensions.py`).
- **Import `db` from `extensions.py` everywhere** (models, app, blueprints).
- **Never call `db.create_all()` in production**—use migrations.
- **Store images (like company logos) as files, not in the database.** Save the file path in the DB.
- **Back up your database before running migrations in production.**

---

## 6. Deployment Notes

- Always run migrations on your production server after deploying new code that changes models:
  ```bash
  flask db upgrade
  ```
- If you need to roll back a migration:
  ```bash
  flask db downgrade
  ```
- Keep your `migrations/` folder under version control.

---

## 7. Troubleshooting

- **Error: No such command 'db'**
  - Ensure Flask-Migrate is installed and registered in your app.
- **RuntimeError: SQLAlchemy instance already registered**
  - Only call `db.init_app(app)` once.
- **ModuleNotFoundError**
  - Ensure all blueprints/files are present and imported correctly.

---

For more details, see the Flask-Migrate documentation: https://flask-migrate.readthedocs.io/ 