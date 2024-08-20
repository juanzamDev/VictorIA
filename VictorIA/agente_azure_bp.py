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
from config import get_client_data
import traceback

# Adición del directorio agents para acceder a los scripts
sys.path.append(os.path.join(os.path.dirname(os.path.abspath("__file__")), "agents"))
import agente_azure_logic

agente_azure_bp = Blueprint('agente_azure_bp', __name__)

system_config_1 = "Un asistente comercial que orienta al cliente sobre características y "\
    "precios de máquinas virtuales de Azure según sus necesidades."

system_config_2 = "El 'Asistente Comercial de Azure' es un agente impulsado por IA de la empresa "\
    "Impresistem. La tarea del asistente es proporcionar información y orientar a los usuarios "\
    "sobre las máquinas virtuales de Azure (Azure VMs) y sus precios, de acuerdo a sus necesidades "\
    "específicas. Solo proporciona respuestas basadas en la documentación oficial de Microsoft y Azure. "\
    "El asistente no debe responder preguntas que no estén relacionadas con los servicios de la nube "\
    "de Microsoft Azure. Es concreto, profesional y amable. Debe pedir aclaraciones e información "\
    "detallada al usuario si su pregunta es ambigua. Las respuestas del asistente deben estar en "\
    "un formato que el usuario pueda entender. Puede usar tablas, listas, diagramas o instrucciones "\
    "paso a paso y también texto en formato MarkDown. Debe formular preguntas para guiar al usuario "\
    "en la búsqueda de la mejor opción de máquina virtual para su proyecto o necesidad. "\
    "Adicionalmente, si el usuario pregunta por una estimación de costos, el asistente debe consultar "\
    "la API de precios de Azure en para buscar el precio de la máquina virtual usando la información "\
    "brindada por el cliente. El asistente usa únicamente los filtros serviceName, armRegionName y "\
    "armSkuName cuando consulta la API. Por defecto, usa la región eastus2 para hacer las búsquedas, "\
    "a menos que el usuario quiera revisar otras regiones. Si no encuentra la VM en la región sugerida, "\
    "consulta de nuevo la API usando otra región válida cercana o con una alternativa similar a la VM "\
    "o con especificaciones parecidas a las dadas por el usuario. \n"\
    "Ejemplos de consulta en la API: \n"\
    "- https://prices.azure.com/api/retail/prices/?api-version=2023-01-01-preview&$filter=serviceName eq 'Virtual Machines' and armRegionName eq 'eastus2' and armSkuName eq 'Standard_F16s' \n"\
    "- https://prices.azure.com/api/retail/prices/?api-version=2023-01-01-preview&$filter=serviceName eq 'Virtual Machines' and armRegionName eq 'westeurope' and (armSkuName eq 'Standard_E4s_v3' or armSkuName eq 'Standard_E4s_v4' or armSkuName eq 'Standard_E4as_v4') \n"\
    "- https://prices.azure.com/api/retail/prices/?api-version=2023-01-01-preview&$filter=serviceName eq 'Virtual Machines' and (armRegionName eq 'eastus2' or armRegionName eq 'southcentralus') and armSkuName eq 'Standard_D16ps_v5'"

@agente_azure_bp.route('/agente_azure')
@login_required
def agent_azure():
    
    # Se obtienen las conversaciones del usuario actual con el agente actual
    actual_agent = db.session.execute(db.select(Agent).where(
        Agent.nombre_agente == 'Agente Azure' 
    )).scalars().first()

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

    return render_template('agente_azure.html', chats_user=chats_user, actual_agent=actual_agent,
                           sorted_chats=sorted_chats, new_chat_uuid=new_chat_uuid)

@agente_azure_bp.route('/agente_azure', methods=['POST'])
@login_required
def agent_azure_post():
    # Se intenta obtener una respuesta con base en el último mensaje del usuario
    try:
        actual_parameters = db.session.execute(db.select(Agent.parametros).where(
        Agent.nombre_agente == 'Agente Azure' 
        )).scalars().first()
        print(actual_parameters)
        
        prompt = request.form['prompt']
        messages = json.loads(request.form['messages'])
        messages.insert(0, {"role": "system", "content": system_config_1})
        messages.insert(1, {"role": "system", "content": system_config_2})
        response = {}
        response['parameters'] = actual_parameters
        response['answer'], response['azureAPI'], messages = agente_azure_logic.generateChatResponse(prompt, messages)

        if len(messages) > 20:
            messages.pop(2)
            messages.pop(2)
        
        #print("MSGs:", type(messages), messages)

        return jsonify(response)
    except:
        print(traceback.format_exc())

        return jsonify({'success': False, 'error': '"No se ha podido obtener una respuesta a tu consulta.'})
    
@agente_azure_bp.route('/get_conversation/<conversationId>')
@login_required
def get_conversation(conversationId):
    # Se obtienen los mensajes de la conversación asociada al ID
    conversation = db.session.execute(db.select(Chat).where(
        Chat.id_conversacion == conversationId)
    ).scalars().first()
    
    return conversation.historico_conversacion

@agente_azure_bp.route('/save_conversation', methods=['POST'])
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
            Agent.nombre_agente == 'Agente Azure' 
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

@agente_azure_bp.route('/get_client/<id>', methods=['GET'])
def get_client(id):
    #  function to get data
    print('Hola mundo!',flush=True)
    rows = get_client_data(id)
    
    if rows:
        return jsonify(rows)
    else:
        return "Cliente no encontrado", 404

@agente_azure_bp.route('/create_pdf', methods=['POST'])
def create_pdf():
    try:
        conversationMessages = request.json['history']
        # print(conversationMessages)
        
        if conversationMessages:
            agente_azure_logic.get_price(conversationMessages)

            return jsonify({'success': True, 'error': '"funciona.'})
        else:
            return jsonify({'success': False, 'error': '"No se ha podido obtener una respuesta a tu consulta.'})
    except:
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': '"No se ha podido obtener una respuesta a tu consulta.'})