from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSON
import datetime
import uuid
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id_usuario = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    nombre_usuario = db.Column(db.String(100), nullable=False)
    correo_usuario = db.Column(db.String(100), nullable=False)
    hash_auth_usuario = db.Column(db.String(100), nullable=False)
    agentes_permitidos = db.Column(db.ARRAY(db.String(100)))
    fecha_usuario = db.Column(db.Date, default=datetime.date.today)

    def get_id(self):
        return (self.id_usuario)
    
    def __repr__(self):
        return (f"Usuario(id_usuario={self.id_usuario!r}, nombre_usuario={self.nombre_usuario!r},"
                f"correo_usuario={self.correo_usuario!r}, hash_auth_usuario={self.hash_auth_usuario!r},"
                f"agentes_permitidos={self.agentes_permitidos!r}, fecha_usuario={self.fecha_usuario!r})")

class Agent(db.Model):
    __tablename__ = 'agente'

    id_agente = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    nombre_agente = db.Column(db.String(100), nullable=False)
    configuracion = db.Column(db.Text)
    parametros = db.Column(JSON)
    tipo = db.Column(db.String(100), nullable=False)
    fecha_agente = db.Column(db.Date, default=datetime.date.today)

    def get_id(self):
        return (self.id_agente)

    def __repr__(self):
        return (f"Agente(id_agente={self.id_agente!r}, nombre_agente={self.nombre_agente!r},"
                f"configuracion={self.configuracion!r}, tipo={self.tipo!r},"
                f"fecha_agente={self.fecha_agente!r})")
    
class Document(db.Model):
    __tablename__ = 'documento'

    id_documento = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    nombre_documento = db.Column(db.String(100), nullable=True)
    embeddings = db.Column(db.ARRAY(JSON), nullable=True)
    fecha_carga = db.Column(db.Date, default=datetime.date.today)
    
    def get_id(self):
        return (self.id_agente)

    def __repr__(self):
        return (f"Documento(id_documento={self.id_documento!r}, nombre_documento={self.nombre_documento!r},"
                f"archivo={self.archivo!r}, fecha_documento={self.fecha_documento!r})")

class Chat(db.Model):
    __tablename__ = 'conversacion'

    id_conversacion = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    id_usuario = db.Column(db.UUID(as_uuid=True), db.ForeignKey('usuario.id_usuario'), nullable=False)
    id_agente = db.Column(db.UUID(as_uuid=True), db.ForeignKey('agente.id_agente'), nullable=False)
    id_documento = db.Column(db.UUID(as_uuid=True), db.ForeignKey('documento.id_documento'))
    nombre_conversacion = db.Column(db.String(100), nullable=False)
    historico_conversacion = db.Column(db.Text, nullable=False)
    tags = db.Column(db.ARRAY(db.String(100)))
    fecha_conversacion = db.Column(db.Date, default=datetime.date.today)

    def get_id(self):
        return (self.id_conversacion)
    
    def __repr__(self):
        return (f"Conversacion(id_conversacion={self.id_conversacion!r}, id_usuario={self.id_usuario!r},"
                f"id_agente={self.id_agente!r}, nombre_conversacion={self.nombre_conversacion!r},"
                f"historico_conversacion={self.historico_conversacion!r}, tags={self.tags!r},"
                f"fecha_conversacion={self.fecha_conversacion!r})")