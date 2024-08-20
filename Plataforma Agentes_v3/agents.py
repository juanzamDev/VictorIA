import sys
import os
import traceback
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user
from .models import Agent, Chat
from . import db

# Adición del directorio agents para acceder a los scripts
sys.path.append(os.path.join(os.path.dirname(os.path.abspath("__file__")), "agents"))
import agent_test

agents = Blueprint('agents', __name__)

# --- Prueba ---
messages = []
messages.append({"role": "system", "content": "Eres uno de los agentes impulsado por IA de la empresa Impresistem."})
# --- Prueba ---

@agents.route('/agent_test')
@login_required
def agent_temp():
    # Se obtienen las conversaciones del usuario actual con el agente actual
    actual_agent_id = db.session.execute(db.select(Agent.id_agente).where(
        Agent.nombre_agente == 'Agente de Pruebas #2' 
    )).scalars().first()

    chats_user = db.session.execute(db.select(Chat).where(
        Chat.id_usuario == current_user.id_usuario).where(
        Chat.id_agente == actual_agent_id
    )).scalars().all()

    return render_template('agent_test.html', chats_user=chats_user)

@agents.route('/agent_test', methods=['POST'])
@login_required
def agent_temp_post():
    # Se intenta obtener una respuesta con base en el último mensaje del usuario
    try:
        prompt = request.form['prompt']
        res = {}
        res['answer'], new_messages = agent_test.generateChatResponse(prompt, messages)

        if len(messages) > 20:
            messages.pop(1)
            messages.pop(1)

        return jsonify(res), 200
    except:
        print(traceback.format_exc())

        return "No hemos podido recuperar la respuesta a tu consulta. Intenta de nuevo"
    
@agents.route('/get_conversation/<conversationId>')
def get_conversation(conversationId):
    # Se obtienen los mensajes de la conversación asociada al ID
    conversation = db.session.execute(db.select(Chat).where(
        Chat.id_conversacion == conversationId)
    ).scalars().first()
    
    return conversation.historico_conversacion
