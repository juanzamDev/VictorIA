import json
import sys
import os
import traceback
import uuid
from collections import defaultdict
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user
from .models import Agent, Chat
from . import db

# Adición del directorio agents para acceder a los scripts
sys.path.append(os.path.join(os.path.dirname(os.path.abspath("__file__")), "agents"))
import agente_test_logic

agente_test_bp = Blueprint('agente_test_bp', __name__)

@agente_test_bp.route('/agente_test')
@login_required
def agent_test():
    # Se obtienen las conversaciones del usuario actual con el agente actual
    actual_agent = db.session.execute(db.select(Agent).where(
        Agent.nombre_agente == 'Agente Pruebas' 
    )).scalars().first()

    print(actual_agent.nombre_agente)

    chats_user = db.session.execute(db.select(Chat).where(
        Chat.id_usuario == current_user.id_usuario).where(
        Chat.id_agente == actual_agent.id_agente
    )).scalars().all()

    sorted_chats = defaultdict(list)
    for chat in chats_user:
        for tag in chat.tags:
            sorted_chats[tag].append(chat)

    # Se genera un nuevo identificador para la conversación nueva que el agente inicia por defecto
    new_chat_uuid = uuid.uuid4()

    return render_template('agente_test.html', chats_user=chats_user, actual_agent=actual_agent,
                           sorted_chats=sorted_chats, new_chat_uuid=new_chat_uuid)

@agente_test_bp.route('/agente_test', methods=['POST'])
@login_required
def agent_test_post():
    # Se intenta obtener una respuesta con base en el último mensaje del usuario
    try:
        prompt = request.form['prompt']
        messages = json.loads(request.form['messages'])
        messages.insert(0, {"role": "system", "content": "Eres uno de los agentes impulsado por IA de la empresa Impresistem."})
        response = {}
        response['answer'], messages = agente_test_logic.generateChatResponse(prompt, messages)

        if len(messages) > 20:
            messages.pop(1)
            messages.pop(1)
        
        return jsonify(response)
    except:
        print(traceback.format_exc())

        return jsonify({'success': False, 'error': '"No se ha podido obtener una respuesta a tu consulta.'})
    
@agente_test_bp.route('/get_conversation/<conversationId>')
@login_required
def get_conversation(conversationId):
    # Se obtienen los mensajes de la conversación asociada al ID
    conversation = db.session.execute(db.select(Chat).where(
        Chat.id_conversacion == conversationId)
    ).scalars().first()
    
    return conversation.historico_conversacion

@agente_test_bp.route('/save_conversation', methods=['POST'])
@login_required
def save_conversation():
    history = request.form['history']
    conversationId = request.form['conversation_id']

    conversation = db.session.execute(db.select(Chat).where(
        Chat.id_conversacion == conversationId)
    ).scalars().first()

    if conversation:
        # Se guarda el histórico en la conversación asociada
        conversation.historico_conversacion = history
        db.session.commit()
        
        return jsonify({'success': True})
    elif conversation is None:
        # Se obtiene el identificador del agente actual
        id_actual_agent = db.session.execute(db.select(Agent.id_agente).where(
            Agent.nombre_agente == 'Agente Pruebas' 
        )).scalars().first()

        # Se crea un nueva conversación si es necesario
        new_conversation = Chat(id_conversacion=conversationId, id_usuario=current_user.id_usuario,
                                id_agente=id_actual_agent, nombre_conversacion="Nueva conversación",
                                historico_conversacion=history, tags=["Nuevo"])
        
        db.session.add(new_conversation)
        db.session.commit()

        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Conversación no encontrada'})
