from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .models import Agent
from . import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    # Se cargan los agentes a los que tiene acceso el usuario que ha iniciado sesión
    agents_allowed = db.session.execute(db.select(Agent).where(
        Agent.nombre_agente.in_(current_user.agentes_permitidos) 
    ).order_by(Agent.nombre_agente.asc())).scalars().all()

    return render_template('profile.html', agents_allowed=agents_allowed)
