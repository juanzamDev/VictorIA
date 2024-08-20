import os
from dotenv import load_dotenv
from urllib.parse import quote
from sqlalchemy import create_engine
import pyodbc
from sqlalchemy.exc import SQLAlchemyError

# Se carga el archivo .env (en caso de existir en el ambiente de desarrollo)
load_dotenv()

# Se especifíca el tipo de ambiente (Dev/Prod)
class Config(object):
    DEBUG = True
    TESTING = False 

# Para el ambiente de desarrollo
# Se cargan las variables de entorno alojadas de forma local en archivo .env
# El acceso al Data Warehouse de Impresistem se debe hacer únicamente desde el ambiente de producción
class DevelopmentConfig(Config):
    OPENAI_KEY = os.getenv('OPENAI_KEY')
    OPENAI_VERSION = os.getenv('OPENAI_VERSION')

    DBNAME = os.getenv('DBNAME_DEV')
    DBHOST = os.getenv('DBHOST_DEV')
    DBPORT = os.getenv('DBPORT_DEV')
    DBUSER = os.getenv('DBUSER_DEV')
    DBPASS = os.getenv('DBPASS_DEV')

    SECRET_KEY = os.getenv('SECRET_KEY')

def get_client_data(id): 
    server=os.getenv("SERVER_DB")
    user=os.getenv("USER_DB")
    password=os.getenv("PASSWORD_DB")
    database=os.getenv("DATABASE_NAME")
    
    try:
        # print("\n--- DIVERS ---\n", pyodbc.drivers())
        connection_string = "DRIVER=ODBC Driver 17 for SQL Server;SERVER={};DATABASE={};UID={};PWD={}".format(server,database,user,password)
        
        # Specifying the ODBC driver, server name, database, etc. directly
        cnxn = pyodbc.connect(connection_string)
        
        # Create cursor
        cursor = cnxn.cursor()
        cursor.execute("SELECT * FROM dbo.tbl_cps_margen_cliente WHERE P_kunnr = ?", id)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            result_dict = {}
            for i, value in enumerate(row):
                result_dict[cursor.description[i][0]] = value

            # query sql server
            parameter = row[3]
            cursor.execute("SELECT * FROM dbo.vw_contacto_cliente_ia where cargo='01-Junta direct' and Nombre_Cliente= ?", parameter)
            additional_data = cursor.fetchall()
            print(additional_data)
            if additional_data:
                additional_data_dicts = []
                for add_row in additional_data:
                    add_result_dict = {}
                    for j, add_value in enumerate(add_row):
                        add_result_dict[cursor.description[j][0]] = add_value
                    additional_data_dicts.append(add_result_dict)
                result_dict['additional_data'] = additional_data_dicts
            
            results.append(result_dict)

        return results

    except pyodbc.Error as e:
        print(str(e),flush=True)
        
        
        
    #     if rows:
    #         for name in rows:
    #             parameter = name[3]
    #             print(parameter)
    #             cursor.execute("SELECT * FROM dbo.tbl_cps_margen_cliente WHERE P_name1 = ?", parameter)
    #             additional_data = cursor.fetchall()
    #             print(additional_data)
    #     else:
    #         print("No se encontraron datos para el cliente.")
 

    #     columns = [desc[0] for desc in cursor.description]
    #     results = []
    #     for row in rows:
    #         result_dict = {}
    #         for i, value in enumerate(row):
    #             result_dict[columns[i]] = value
    #         results.append(result_dict)
    #     print(results)

        
    #     return results
        
    # except SQLAlchemyError as e:
    #     print("Error en la conexión:", e)
    
    
# Para el ambiente de producción
# Se cargan las variables de entorno configuradas en Azure Web Services
# OPENAI_KEY, SECRET_KEY y las credenciales de acceso a las BD de agentes y bodega de datos
class ProductionConfig(Config):
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_API_VERSION = os.getenv('OPENAI_API_VERSION')

    IA_DB_NAME = os.getenv('IA_NAME_DB')
    IA_DB_HOST = os.getenv('IA_PASSWORD_DB')
    IA_DB_PORT = os.getenv('IA_PORT_DB')
    IA_DB_USER = os.getenv('IA_SERVER_DB')
    IA_DB_PASS = os.getenv('IA_USER_DB')

    BI_DW_NAME = os.getenv('BI_NAME_DB')
    BI_DW_HOST = os.getenv('BI_PASSWORD_DB')
    BI_DW_PORT = os.getenv('BI_PORT_DB')
    BI_DW_USER = os.getenv('BI_SERVER_DB')
    BI_DW_PASS = os.getenv('BI_USER_DB')

    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # server=os.getenv("SERVER_DB")
    # user=os.getenv("USER_DB")
    # password=os.getenv("PASSWORD_DB")
    # database=os.getenv("DATABASE_NAME")
 
    # contrasena_codificada = quote(password)
 
    # connection_string = "mssql+pyodbc://{}:{}@{}/{}?driver=ODBC+Driver+17+for+SQL+Server".format(user,contrasena_codificada,server,database)
 
    # db_engine = create_engine(url=connection_string)

# Se establece la configruación de la aplicación con base en el tipo de ambiente (Dev/Prod)
config = {
    'development': DevelopmentConfig,
    'testing': DevelopmentConfig,
    'production': ProductionConfig
}
