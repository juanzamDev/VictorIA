# Plataforma de agentes expertos de Impresistem

## 🌟 Introducción
Este proyecto es una integración de la API de Azure OpenAI (con la opción de usar otros modelos de lenguaje) con una aplicación web Flask/Bootstrap para el diseño de una interfaz que facilite al usuario final la interacción con los agentes creados en diferentes procesos/áreas de Impresistem. 

## 🔧 Pre-requisitos
Antes de comenzar, asegúrate de tener los siguientes requisitos:
- Python 3.11 o superior
- Acceso a Azure y Azure DevOps
- Clave API de Azure OpenAI
- Para el caso de la ejecución local es necesario tener instalado Docker Desktop

## 📦 Instalación

1. **Clonar el repositorio:**
   ```sh
   git clone https://Alix-IA-Impresistem@dev.azure.com/Alix-IA-Impresistem/Plataforma%20Agentes/_git/Plataforma%20Agentes
   ```

## ⚙️ Configuración

1. **Configuración de Variables de Entorno:**
   - Crear un archivo `.env` en el directorio app para el ambiente de desarrollo.
   - Agregar las claves API y detalles de la base de datos:
     ```
     FLASK_DEBUG = 1
     FLASK_APP = __init__.py
     FLASK_RUN_PORT = 8000
     FLASK_RUN_HOST = 0.0.0.0

     OPENAI_KEY = 509edbed2f8f4b13b33b34464f6b66b1
     OPENAI_VERSION = 2023-12-01-preview

     DBNAME_DEV = nombre_bd_dockercompose
     DBHOST_DEV = nombre_servicio_bd_dockercompose
     DBPORT_DEV = puerto_bd_dockercompose
     DBUSER_DEV = usuario_bd_dockercompose
     DBPASS_DEV = contraseña_bd_dockercompose

     SECRET_KEY = uuid_secreto
     ```
   - El valor de SECRET_KEY puede ser generado mediante la librería "secrets" de Python con el siguiente comando:
     ```python
     import secrets
     print(secrets.token_hex(16))
     ```

2. **Configuración de Azure:**
   - En el ambiente de producción, asegúrate de configurar las variables de entorno en Azure Web Services.

3. **Lanzar aplicación:**
   - Si ejecutas el proyecto de forma local, asegúrate de tener en ejecución Docker Desktop
   - Usa el siguiente comando (localmente en el CMD de tu sistema operativo, o configurando el arranque en la VM de Azure) para ejeuctar la aplicación:
     ```sh
     docker-compose up -d --build
     ```

## 🚀 Despliegue en Azure

1. **Preparar el código para producción:**
   - Asegúrate de que el código esté listo para el despliegue y haya sido probado localmente.

2. **Configurar Azure DevOps:**
   - Crea un nuevo proyecto en Azure DevOps.
   - Configura un pipeline de CI/CD que se conecte a tu repositorio de código.

3. **Configuración del Pipeline:**
   - En el pipeline, añade los pasos para construir tu aplicación y desplegarla en Azure (ya sea en una máquina virtual o Kubernetes).

4. **Ejecutar el Pipeline:**
   - Ejecuta el pipeline y monitorea el proceso de despliegue.

5. **Verificar el Despliegue:**
   - Una vez completado el despliegue, verifica que la aplicación esté funcionando correctamente en el entorno de Azure.

## 🖥️ Uso de la Aplicación

1. **Acceder a la Aplicación:**
   - Abre la URL de tu aplicación desplegada en Azure.

2. **Interactuar con el Chatbot:**
   - Utiliza el chatbot para hacer preguntas a cada agente.

## 🐛 Solución de Problemas

Si encuentras algún problema:
1. **Revisa los Logs:**
   - Verifica los logs de la aplicación para identificar posibles errores.

2. **Consultar la Documentación:**
   - Asegúrate de haber seguido todos los pasos de instalación y configuración.

## 🤝 Contribuciones

Las contribuciones son siempre bienvenidas. Si tienes alguna sugerencia para mejorar este proyecto, no dudes en contribuir.
