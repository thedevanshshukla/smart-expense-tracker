from flask import Flask
from flask_login import LoginManager
from datetime import datetime
from config import Config
from models import db, User
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp
from flask import render_template as rt
from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import generate_csrf



app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)
# Initialize extensions
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@app.route('/')
def home():
    return rt('home.html')
# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)

# Inject current year globally for templates
@app.context_processor
def inject_now():
    return {'current_year': datetime.now().year}
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)
@app.after_request
def add_cache_control_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# Create database tables and run
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False)


# change layout
# filter not working 
#add delete option
