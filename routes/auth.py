from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import db
from models import Usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Buscar usuario en SQL Database
        user = Usuario.query.filter_by(email=email).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['rol'] = user.rol
            flash(f'Bienvenido/a de nuevo, {user.nombre} ({user.rol})', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciales incorrectas. Verifique correo y contraseña.', 'error')
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('auth.login'))
