import os
import sys
import openai
import traceback

# Adición del directorio agents para acceder a los scripts
sys.path.append(os.path.join(os.path.dirname(os.path.abspath("__file__"))))
import config

# Se determina el entorno y se carga la versión y el API Key de Azure OpenAI
if 'DBNAME_DEV' not in os.environ:
    openai.api_key = config.ProductionConfig.OPENAI_API_KEY
    api_version = config.ProductionConfig.OPENAI_API_VERSION
else:
    openai.api_key = config.DevelopmentConfig.OPENAI_KEY
    api_version = config.DevelopmentConfig.OPENAI_VERSION

# Se especifícan la URL y la versión del despliegue del modelo de OpenAI (Azure Impresistem)
client = openai.AzureOpenAI(
    azure_endpoint="https://impresistemia.openai.azure.com/",
    api_version=api_version,
    api_key=openai.api_key
)

# Se define la función que envía los mensajes al modelo y retorna sus repsuestas
def generateChatResponse(prompt, messages):
    messages.append({"role": "user", "content": prompt})

    # Se crea el objeto en donde se definen los parámetros de funcionamiento del modelo
    response = client.chat.completions.create(
        model="impresistem-gpt-35-turbo",
        frequency_penalty=0,
        max_tokens=4096,
        presence_penalty=0,
        temperature=1,
        top_p=1,
        messages=messages
    )

    # Se recupera la respuesta y se procesa para ser mostrada en la intefaz web
    try:
        answer = response.choices[0].message.content
        messages.append({"role": "assistant", "content": answer})
    except:
        print(traceback.format_exc())
        answer = "No hemos podido responder a tu solicitud. Intenta de nuevo"
    
    return answer, messages

