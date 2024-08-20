import hashlib
from flask_login import login_user, login_required, logout_user
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from .models import User, Agent
from . import db

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    # Se leen los datos del formulario de inicio de sesión
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    # Se busca al usuario en la BD y se calcula el hash de la clave introducida
    user = db.session.execute(db.select(User).where(User.correo_usuario == email)).scalars().first()
    encoded_pass_in = password.encode('UTF-8')
    hash_pass_in = hashlib.sha256(encoded_pass_in).hexdigest()

    # Si el usuario no existe o los hash no coinciden se notifica en un mensaje
    if not user or not (user.hash_auth_usuario == hash_pass_in):
        flash('Credenciales inválidas. Verifica e intenta de nuevo.', "error")
        return redirect(url_for('auth.login'))

    # Se permite el acceso si las credenciales son váildas
    login_user(user, remember=remember)

    return redirect(url_for('main.profile'))

@auth.route('/signup', methods=['GET'])
def signup():
    # Se muestran los agentes disponibles para asignar el acceso
    agents = db.session.execute(db.select(Agent)).scalars().all()

    return render_template('signup.html', agents=agents)

@auth.route('/getAgents', methods=['GET'])
def get_agents():  
    
    # Consulta la base de datos para obtener todos los registros en la tabla Agent    
    agents = db.session.query(Agent).all()     
    
    # Crea una lista con los nombres de los agentes utilizando una comprensión de lista   
    agent_names = [agent.nombre_agente for agent in agents]          
    
    # Devuelve la lista de nombres de agentes en formato JSON
    return jsonify(agent_names)

@auth.route('/signup', methods=['POST'])
def signup_post():
    # Se leen los datos del formulario de registro
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    agents = request.form.getlist('agents')

    # Se comprueba si el usuario ya existe en la BD
    user = db.session.execute(db.select(User).where(User.correo_usuario == email)).scalars().first()

    # Si el usuario ya existe se notifica en un mensaje
    if user:
        flash('¡El usuario ya está registrado!', 'warning')
        return redirect(url_for('auth.signup'))

    # Se creal el nuevo usuario y se guarda el hash de la clave
    encoded_pass = password.encode('UTF-8')
    new_user = User(nombre_usuario=name, correo_usuario=email,
                    hash_auth_usuario=hashlib.sha256(encoded_pass).hexdigest(),
                    agentes_permitidos=agents)

    # Se añade el registro a la BD
    db.session.add(new_user)
    db.session.commit()

    flash('¡Usuario registrado con exito!')

    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    # Se cierra la sesión del usuario actual
    logout_user()
    return redirect(url_for('main.index'))
