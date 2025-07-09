
from flask import Blueprint, render_template , redirect, url_for, flash,  session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import db, User
from .forms import SignupForm, LoginForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# ------------------------
# Sign Up
# ------------------------
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('User already exists. Please log in.', 'danger')
            return redirect(url_for('auth.login'))

        user = User(
            email=form.email.data,
            password=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/signup.html', signup_form=form)

# ------------------------
# Login
# ------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            # Optional: store minimal session data
            session['user_id'] = user.id
            session['user_name'] = user.email.split('@')[0]
            return redirect(url_for('dashboard.dashboard_home'))  # <- Must match route
        else:
            flash('Invalid credentials or user not found.', 'danger')

    return render_template('auth/login.html', login_form=form)

# ------------------------
# Logout
# ------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))
