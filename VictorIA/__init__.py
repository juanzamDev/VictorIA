import os
from . import config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Inicializa SQLAlchemy para todo el proyecto
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    # Se determina el ambiente (Dev/Prod) y se cargan las variables de entorno
    if 'DBNAME_DEV' not in os.environ:
        app.config.from_object(config.config['production'])

        # Se asignan las variables para las cadenas de conexión a la BD en Azure
        database = app.config.get('IA_DB_NAME')
        user = app.config.get('IA_DB_USER')
        password = app.config.get('IA_DB_PASS')
        host = app.config.get('IA_DB_HOST')
        port = app.config.get('IA_DB_PORT')
        
        db_uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        
    else:
        app.config.from_object(config.config['development'])

        # Se asignan las variables para la cadena de conexión a la BD local
        database = app.config.get('DBNAME')
        user = app.config.get('DBUSER')
        password = app.config.get('DBPASS')
        host = app.config.get('DBHOST')
        port = app.config.get('DBPORT')
        db_uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

    # Se crea la cadena de conexión a la BD y la clave de la aplicación
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

    # Se inicializa la aplicación
    db.init_app(app)

    # Se crea el sistema de login y sesión
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = u"Por favor, inicia sesión para continuar."
    login_manager.init_app(app)

    from .models import User

    # Se usa el id_usuario para almacenar los datos de sesión
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # Blueprint para las rutas de autenticación
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # Blueprint para las rutas de perfil y página inicial
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Blueprint para el agente de pruebas
    from .agente_test_bp import agente_test_bp as agent_test_blueprint
    app.register_blueprint(agent_test_blueprint, url_prefix='/agente_test')

    # Blueprint para el agente Azure
    from .agente_azure_bp import agente_azure_bp as agent_azure_blueprint
    app.register_blueprint(agent_azure_blueprint, url_prefix='/agente_azure')

    # Blueprint para el agente Licitaciones
    from .agente_licitaciones_bp import agente_licitaciones_bp as agent_licitaciones_blueprint
    app.register_blueprint(agent_licitaciones_blueprint, url_prefix='/agente_licitaciones')


    return app
