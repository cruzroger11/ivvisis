from functools import wraps
from flask import session, redirect, url_for, flash
from models import Usuario

def get_current_user():
    user_id = session.get('user_id')
    # Dado que Usuario hereda de Persona, query.get(user_id) funcionará si user_id es el ID de la Persona
    return Usuario.query.get(user_id) if user_id else None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, inicie sesión para acceder.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return redirect(url_for('auth.login'))
            
            # Administrador siempre tiene acceso total
            if user.rol == 'Administrador':
                return f(*args, **kwargs)
                
            if user.rol not in roles:
                flash(f'Acceso denegado. Su rol de "{user.rol}" no tiene permiso para esta acción.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

