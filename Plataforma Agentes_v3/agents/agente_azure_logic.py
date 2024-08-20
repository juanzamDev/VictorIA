import json
import os
import sys
import openai
import traceback
from flask import render_template
from weasyprint import HTML,CSS
import requests
from PyPDF2 import PdfMerger

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

def searchAzureAPI(armRegionName, serviceName, armSkuName):
    # Se construye la URL de la API con los parámetros
    url = f"https://prices.azure.com/api/retail/prices/?api-version=2023-01-01-preview&$filter=serviceName eq '{serviceName}' and armRegionName eq '{armRegionName}' and armSkuName eq '{armSkuName}'"
    
    # Se configura los encabezados, incluyendo la autenticación si es necesario
    headers = {
        "Content-Type": "application/json"
    }
    
    # Realiza la solicitud a la API
    responseAPI = requests.get(url, headers=headers)
    
    # Verifica que la respuesta sea exitosa (código 200)
    if responseAPI.status_code == 200:
        # Procesa la respuesta
        data = responseAPI.json()
        return data
    else:
        print(f"Error en la solicitud: {responseAPI.status_code}")

        return None


# Se define la función que envía los mensajes al modelo y retorna sus repsuestas
def generateChatResponse(prompt, messages):
    messages.append({"role": "user", "content": prompt})
    tools = [
        {
            "type": "function",
            "function": {
                "name": "obtener_azure_vms",
                "description": "Obtener precios y características de VMs de Azure",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "armRegionName": {
                            "type": "string",
                            "description": "La región de ubicación de la VM (por ejemplo, eastus2)",
                        },
                        "serviceName": {
                            "type": "string",
                            "description": "El nombre del servicio en Azure (en este caso, Virtual Machines)",
                            "enum": ["Virtual Machines"],
                        },
                        "armSkuName": {
                            "type": "string",
                            "description": "El nombre del identificador de la VM (por ejemplo, Standard_D32ls_v5)",
                        },
                    },
                    "required": ["armRegionName", "serviceName", "armSkuName"],
                },
            },
        }
    ]

    # Se crea el objeto en donde se definen los parámetros de funcionamiento del modelo
    response = client.chat.completions.create(
        model="impresistem-gpt-35-turbo",
        frequency_penalty=0,
        max_tokens=4096,
        presence_penalty=0,
        temperature=1,
        top_p=1,
        tools=tools,
        tool_choice="auto",
        messages=messages
    )

    # Se recupera la respuesta y se procesa para ser mostrada en la intefaz web
    try:
        answer = response.choices[0].message
    
        # Guardar la respuesta en el histórico y mostrarla en la ventana de conversación
        if answer.content:
            messages.append({"role": "assistant", "content": answer.content})

            return answer.content, messages
        elif answer.tool_calls:
            # Lógica para procesar las consultas con base en los argumentos generados
            args = answer.tool_calls[0].function.arguments
            argsAPI = json.loads(args)
            responseAPI = searchAzureAPI(argsAPI["armRegionName"], argsAPI["serviceName"], argsAPI["armSkuName"])

            messages.append({"role": "assistant", 
                             "content": "Dame un resumen detallado de la siguiente información: " + str(responseAPI)})
            
            # get_price(responseAPI)    Aca se llama la funcion para crear el PDF

            final_answer  = client.chat.completions.create(
                model="impresistem-gpt-35-turbo",
                frequency_penalty=0,
                max_tokens=4096,
                presence_penalty=0,
                temperature=1,
                top_p=1,
                messages=messages
            )

            if final_answer.choices[0].message.content:
                messages.pop()
                messages.append({"role": "assistant", "content": final_answer.choices[0].message.content})

            return final_answer.choices[0].message.content, responseAPI, messages
    except:
        print(traceback.format_exc())
        answer = "No hemos podido responder a tu solicitud. Intenta de nuevo"

def get_price(resAPI):    
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css_path = os.path.join(root_path,'static','css','style_pdf.css')
    files_path = os.path.join(root_path,'static','files','cotizacion.pdf')
    images_path = os.path.join(root_path,'static','images','logo.png')  
    rendered = render_template("cotizacion.html",logo = images_path,data=resAPI) 
    HTML(string=rendered).write_pdf(files_path,stylesheets=[CSS(css_path)])
    get_pdf(files_path)

def get_pdf(first_page):
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_terms_path = os.path.join(root_path,'static','files','terminos.pdf')
    pdf_final_path = os.path.join(root_path,'static','files','cotizacionfinal.pdf')
    merger = PdfMerger()
    with open(pdf_final_path,'wb') as file:
        merger.append(first_page)
        merger.append(pdf_terms_path)
        merger.write(file)
    

