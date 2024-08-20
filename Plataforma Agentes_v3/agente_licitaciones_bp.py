import json
import sys
import os
import traceback
import uuid
import tempfile
import json
from sqlalchemy import join
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound
from collections import defaultdict
from . import db
from flask import Blueprint, jsonify, render_template, request, url_for, redirect, flash, session
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from .models import Agent, Chat, Document

# Adición del directorio agents para acceder a los scripts
sys.path.append(os.path.join(os.path.dirname(os.path.abspath("__file__")), "agents"))
import agente_licitaciones_logic

agente_licitaciones_bp = Blueprint('agente_licitaciones_bp', __name__)

# Crear una carpeta temporal global cuando se define el Blueprint
temp_dir_global = tempfile.mkdtemp()

system_config_1 = "Un asistente legal que ayuda a los usuarios a estudiar, analizar y resumir "\
    "documentos de procesos licitatorios para encontrar información relevante y responder preguntas sobre estos."

@agente_licitaciones_bp.route('/agente_licitaciones')
@login_required
def agent_licitaciones():
    # Se obtienen las conversaciones del usuario actual con el agente actual
    actual_agent = db.session.execute(db.select(Agent).where(
        Agent.nombre_agente == 'Agente Licitaciones' 
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

    return render_template('agente_licitaciones.html', actual_agent=actual_agent,
                           sorted_chats=sorted_chats, new_chat_uuid=new_chat_uuid)

@agente_licitaciones_bp.route('/load_files_rag', methods=['POST'])
@login_required
def load_files_rag():

    # Obtener los archivos del formulario
    files = request.files.getlist('file')
    
    if not files:
        flash('No se ha recibido ningún archivo', 'error')
        return redirect(url_for('agente_licitaciones_bp.agent_licitaciones'))
    
    if files:
        try:
            # Crear una carpeta temporal para almacenar los archivos
            temp_dir = temp_dir_global
            
            for file in files:
                if file and (file.filename.endswith('.pdf') or file.filename.endswith('.doc') or file.filename.endswith('.docx')):
                    filename = secure_filename(file.filename)
                    
                    # Crear la ruta del archivo temporal
                    temp_file_path = os.path.join(temp_dir, filename)
                    
                    # Guardar el archivo temporalmente
                    file.save(temp_file_path)

                    # Subir el archivo a Azure Blob Storage
                    #agente_licitaciones_logic.upload_to_azure_blob(file_stream, filename, conversation_id)  

            session['temp_dir'] = temp_dir
          
            flash('Archivos cargados exitosamente', 'success')
        except Exception as e:
            print(e)
            flash('Error al guardar los archivos', 'error')
        
    else:
        flash('No se ha recibido ningún archivo', 'error')
    
    return redirect(url_for('agente_licitaciones_bp.agent_licitaciones'))
   
@agente_licitaciones_bp.route('/agente_licitaciones', methods=['POST'])
@login_required
def agent_licitaciones_post():
    # Se intenta obtener una respuesta con base en el último mensaje del usuario
  
        prompt = request.form['prompt']
        messages = json.loads(request.form['messages'])   
        messages.insert(0, {"role": "system", "content": system_config_1})
        response = {}
        actual_id = request.form['actual_id']
        temp_dir = session.get('temp_dir')

       # Obtener el id_documento asociado a la conversación
        id_documento = db.session.query(Chat.id_documento).filter(Chat.id_conversacion == actual_id).scalar()

        if id_documento:
            # Obtener los embeddings del documento asociado
            embeddings_act = db.session.query(Document.embeddings).filter(Document.id_documento == id_documento).scalar()
        else:
            embeddings_act = 12
            print("No se encontraron embeddings para la conversación actual.")
               
        response['answer'], messages, embeddings = agente_licitaciones_logic.generateChatResponse(prompt, messages, temp_dir, embeddings_act)

        try:
            # Buscar el id del documento asociado a esta conversación utilizando la llave foránea id_conversacion
            id_documento_conversacion = db.session.query(Chat.id_documento).filter_by(id_conversacion=actual_id).scalar()
            print("Se encontró un documento asociado a esta conversación.")
            
            new_doc_uuid = uuid.uuid4()

            # Verificar si el documento ya está en la base de datos
            try:
                existing_document = Document.query.filter_by(id_documento=id_documento_conversacion).one()
                print("El documento asociado a esta conversación ya está en la base de datos.")
            except NoResultFound:
                print("No se encontró ningún documento asociado a esta conversación en la base de datos.")
                
                # Crear un nuevo documento
                new_document = Document(id_documento=new_doc_uuid, nombre_documento="Nuevo documento", embeddings=embeddings)

                session['new_doc_uuid'] = new_doc_uuid

                print(f"este es el id del doc primero {id_documento_conversacion}")

                # Agregar y confirmar el nuevo documento en la base de datos
                db.session.add(new_document)
                db.session.commit()
                print("Se ha creado y guardado un nuevo documento asociado a esta conversación.")
            
            if len(messages) > 20:
                messages.pop(1)
                messages.pop(1)
            
            return jsonify(response)

        except Exception as e:
            print(traceback.format_exc())
            return jsonify({'success': False, 'error': 'No se ha podido obtener una respuesta a tu consulta.'})

    
@agente_licitaciones_bp.route('/get_conversation/<conversationId>')
@login_required
def get_conversation(conversationId):
    
    # Se obtienen los mensajes de la conversación asociada al ID
    conversation = db.session.execute(db.select(Chat).where(
        Chat.id_conversacion == conversationId)
    ).scalars().first()
    
    return conversation.historico_conversacion

@agente_licitaciones_bp.route('/save_conversation', methods=['POST'])
@login_required
def save_conversation():
    history = request.form['history']
    conversationId = request.form['conversation_id']
    id_documento = session.get('new_doc_uuid')

    print(f"este es el id del doc {id_documento}")

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
            Agent.nombre_agente == 'Agente Licitaciones' 
        )).scalars().first()

       # Crear un alias para la tabla Document
        """DocumentAlias = aliased(Document)

        # Obtener el id_documento como clave foránea
        id_documento = db.session.query(DocumentAlias.id_documento).\
            join(Chat, Chat.id_documento == DocumentAlias.id_documento).\
            filter(Chat.id_conversacion == conversationId).scalar()

        # Verificar si se obtuvo un resultado
        if id_documento is not None:"""
            # Crear una nueva conversación si es necesario
        new_conversation = Chat(id_conversacion=conversationId,
                                id_usuario=current_user.id_usuario,
                                id_agente=id_actual_agent,
                                id_documento=id_documento,
                                nombre_conversacion="Nueva conversación",
                                historico_conversacion=history,
                                tags=["Nuevo"])

        # Agregar la nueva conversación a la sesión y confirmar los cambios
        db.session.add(new_conversation)
        db.session.commit()

        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Conversación no encontrada'})