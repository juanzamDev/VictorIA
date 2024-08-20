import os, sys
import traceback
import openai
import tiktoken
import json
from shutil import rmtree
from llama_index.core import SimpleDirectoryReader, Settings, set_global_tokenizer
from llama_index.core.indices.prompt_helper import PromptHelper
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from azure.storage.blob import BlobServiceClient

# Adición del directorio agents para acceder a los scripts
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))
import config

# Cadena de conexión
CONNECT_STR="DefaultEndpointsProtocol=https;AccountName=victoriaimpresistem;AccountKey=CHLzMcx8O6Ra5DfhcywrZaqEHbt7DK/O9b59k0f37UiUrRwOTD6aR/Fswst+lDvfIKYRbkBJPIwE+AStl+f+sA==;EndpointSuffix=core.windows.net"

# Se determina el entorno y se carga la versión y el API Key de Azure OpenAI
if 'DBNAME_DEV' not in os.environ:
    openai.api_key = config.ProductionConfig.OPENAI_API_KEY
    api_version = config.ProductionConfig.OPENAI_API_VERSION
else:
    openai.api_key = config.DevelopmentConfig.OPENAI_KEY
    api_version = config.DevelopmentConfig.OPENAI_VERSION

# Se especifícan los parámetros del LLM de OpenAI (Azure Impresistem)
llmAzureOpenAI = AzureOpenAI(
    deployment_name="impresistem-gpt-35-turbo",
    model="gpt-35-turbo-16k",
    azure_endpoint="https://impresistemia.openai.azure.com/",
    api_version=api_version,
    api_key=openai.api_key
)

# Se especifícan los parámetros del modelo de embeddings de OpenAI (Azure Impresistem)
embedAzureOpenAI = AzureOpenAIEmbedding(
    deployment_name="impresistem-text-embedding-ada-002",
    model="text-embedding-ada-002",
    azure_endpoint="https://impresistemia.openai.azure.com/",
    api_version=api_version,
    api_key=openai.api_key
)


def rag_pipeline(prompt, temp_dir, embeddings_act):

    set_global_tokenizer(tiktoken.encoding_for_model("gpt-35-turbo-16k").encode)

    llm = llmAzureOpenAI
    embed_model = embedAzureOpenAI

    node_parser = SentenceSplitter.from_defaults()

    prompt_helper = PromptHelper(
        context_window=3900,
        num_output=256,
        chunk_overlap_ratio=0.1,
        separator = " ",
        chunk_size_limit=None
    )

    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.node_parser = node_parser
    Settings.prompt_helper = prompt_helper
    Settings.context_window = 3900
    
    pdf_files_present = any(file.endswith('.pdf') for file in os.listdir(temp_dir))

    if pdf_files_present:
        # Embeddings creacion solo si hay archivos PDF
        documents = SimpleDirectoryReader(input_dir=temp_dir).load_data()
        vector_index = VectorStoreIndex.from_documents(documents) 
        vector_index.set_index_id("vector_index")
        vector_index.storage_context.persist(temp_dir)
    else:
        print("No se encontraron archivos PDF en la carpeta, se omite la creación de embeddings.")

    def cargar_embeddings(ruta_archivo):
        embeddings = []
        archivos = ["default__vector_store.json", "docstore.json", "index_store.json"]

        for archivo in archivos:
            archivo_path = os.path.join(ruta_archivo, archivo)
            if os.path.exists(archivo_path):
                with open(archivo_path, 'r') as file:
                    data = json.load(file)
                    embeddings.append(data)
            else:
                print(f"Advertencia: No se encontró el archivo {archivo_path}, se omite la carga de este embedding.")

        # Convertir cada elemento de la lista en un array JSON solo si se cargó algún embedding
        embeddings_arrays = [json.dumps(embedding) for embedding in embeddings] if embeddings else []

        return embeddings_arrays

    def actualizar_embeddings(temp_dir, embeddings_act):
        archivos = ["default__vector_store.json", "docstore.json", "index_store.json"]

        for archivo, embedding_json in zip(archivos, embeddings_act):
            # Ruta completa al archivo en el directorio temporal
            archivo_path = os.path.join(temp_dir, archivo)

            # Convertir el string JSON en un objeto Python para los nuevos datos
            nuevo_embedding_data = json.loads(embedding_json)

            # Leer y comparar con los datos existentes si el archivo ya existe
            if os.path.exists(archivo_path):
                with open(archivo_path, 'r') as file:
                    # Cargar los datos existentes
                    existing_embedding_data = json.load(file)

                # Comparar los datos existentes con los nuevos
                if nuevo_embedding_data != existing_embedding_data:
                    # Los datos son diferentes, actualizar el archivo
                    with open(archivo_path, 'w') as file:
                        json.dump(nuevo_embedding_data, file, indent=4)
                # Si son iguales, no se realiza ninguna acción
            else:
                # Si el archivo no existe, se crea y se escriben los nuevos datos
                with open(archivo_path, 'w') as file:
                    json.dump(nuevo_embedding_data, file, indent=4)

    
    # Llamado de la funcion
    embeddings = cargar_embeddings(temp_dir)

    # Eliminamos el o los pdfs una vez cargados los embeddings a bd
    for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path) and filename.endswith(".pdf"):
                    os.remove(file_path)
            except Exception as e:
                print(f"No se pudo eliminar {file_path}: {e}")

    # Validación para arrancar la función de actalizar embeddings
    if not isinstance(embeddings_act, (int)):
        actualizar_embeddings(temp_dir, embeddings_act)
    else:
        print("No se encontraron embeddings para la conversación actual.")


    # Lectura de embeddings
    storage_context = StorageContext.from_defaults(persist_dir=temp_dir)  
    vector_index = load_index_from_storage(storage_context, index_id="vector_index")

    query_engine = vector_index.as_query_engine(response_mode="compact")
    response = str(query_engine.query(prompt))

    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(file_path) and filename.endswith(".json"):
                os.remove(file_path)
                print(f"Archivo {file_path} eliminado correctamente.")
            elif os.path.isdir(file_path):
                rmtree(file_path)
                print(f"Directorio {file_path} eliminado correctamente.")
        except Exception as e:
            print(f"No se pudo eliminar {file_path}: {e}")

    return response, embeddings

# Se define la función que envía los mensajes al modelo y retorna sus respuestas
def generateChatResponse(prompt, messages, temp_dir, embeddings_act):
    messages.append({"role": "user", "content": prompt})

    # Se crea el objeto en donde se definen los parámetros de funcionamiento del modelo
    response, embeddings = rag_pipeline(prompt, temp_dir, embeddings_act)

    # Se recupera la respuesta y se procesa para ser mostrada en la intefaz web
    try:
        answer = response
        messages.append({"role": "assistant", "content": answer})
    except:
        print(traceback.format_exc())
        answer = "No hemos podido responder a tu solicitud. Intenta de nuevo"
    
    return answer, messages, embeddings

def upload_to_azure_blob(file_stream, file_name, conversation_id):
    if not conversation_id:
        raise ValueError("El conversation_id está vacío o no es válido")
    
    blob_service_client = BlobServiceClient.from_connection_string(CONNECT_STR)

    # Subir el archivo al Blob Storage
    blob_name = f'{conversation_id}/{file_name}'
    blob_client = blob_service_client.get_blob_client(container='licitaciones', blob=blob_name)

    blob_client.upload_blob(file_stream, overwrite=True)