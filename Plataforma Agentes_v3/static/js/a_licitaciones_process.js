function showQAChatBot(userAvatar, botAvatar) {
    // Se obtienen los mensajes de la conversación actual
    let actual_messages = extractMessagesToJson()
    // Se extrae la pregunta del usuario en el campo de consulta
    const question = $("#chat-input").val();
    let html_question = '';
  
    // Se crea el componente HTML que contiene la pregunta del usuario
    html_question += `
      <div class="list-group-item list-group-item-action d-flex gap-3 pt-4">
        <img src=${userAvatar} alt="user" width="32" height="32" class="rounded-circle">
        <div">
          <h6>Tú</h6>
          <div>
            <p class="opacity-75">
              <md-block>${question}</md-block>
            </p>
          </div>
        </div>
      </div>
      `;
    // Se limpia el campo de consulta y se añade la pregunta del usuario a la venta de mensajes
    $("#chat-input").val('');
    $("#list-group").append(html_question);

    // Se obtiene el id de la conversación seleccionada
    actual_conversation_id = $('#list-group').data('conversation-id');

    // Se invoca el agente con la pregunta, mensajes y id actual como parámetros
    $.ajax({
      type: "POST",
      url: "/agente_licitaciones/agente_licitaciones",
      data: {
        'prompt': question,
        'messages': actual_messages,
        "actual_id": actual_conversation_id
      },
      // Se crea el componente HTML que contiene la respuesta generada por el agente
      success: function(data) {
        let html_answer = '';
        html_answer += `
          <div class="list-group-item list-group-item-action d-flex gap-3 pt-4">
            <img src=${botAvatar} alt="bot" width="32" height="32" class="rounded-circle">
            <div>
              <h6>Agente</h6>
              <div>
                <p>
                  <md-block>${data.answer}</md-block>
                </p>
              </div>
            </div>
          </div>
          `;
  
        // Se añade la respuesta del agente a la venta de mensajes
        $("#list-group").append(html_answer);
  
        // Se guardan los mensajes actuales de la conversación en un formato JSON
        messagesJSON = extractMessagesToJson();
        
        // Se guarda el histórico de la conversación en la BD
        saveRealTimeChat(messagesJSON, actual_conversation_id);
  
        console.log("Respuesta del agente obtenida exitosamente.");
      },
      error: function() {
        console.log("Error al obtener respuesta el agente.");
      }
    });
  };
  
  function extractMessagesToJson() {
    // Se seleccionan todos los mensajes actuales en la ventana de chat
    let messages = [];
  
    // Por cada mensaje se dentifica si es del usuario o del agente y se borran los saltos de línea (\n)
    $('#list-group .list-group-item').each(function() {
      let sender = $(this).find('h6').text().includes('Tú') ? 'user' : 'assistant';
      let message_text = $(this).find('md-block').text();
  
      // Se guardan los mensajes y sus emisores en un arreglo
      messages.push({
        role: sender,
        content: message_text
      });
    });
  
    // Se convierte el arreglo de mensajes a un formato JSON
    let messagesJSON = JSON.stringify(messages);
  
    return messagesJSON;
  }
  
  function saveRealTimeChat(messages_json, actual_conversation_id) {
    // Se obtiene el identificador de la conversación actual y los mensajes en formato JSON para guardarlos en la BD
    $.ajax({
      type: "POST",
      url: "/agente_licitaciones/save_conversation",
      data: {
        'history': messages_json,
        'conversation_id': actual_conversation_id
      },
      success: function() {
        console.log("¡Conversación guardada!");
      },
      error: function() {
        console.log("Error al guardar conversación.");
      }
    });
  }

  function getFilesChat() {
    // Obtener el identificador de la conversación actual desde el atributo de datos HTML
    var actual_conversation_id = $('#list-group').data('conversation-id');
   
    // Verificar si se ha seleccionado al menos un archivo
    var files = $('#file')[0].files;
    if (files.length === 0) {
        console.log("Debes seleccionar al menos un archivo.");
        return;
    }

    // Crear un objeto FormData para enviar los archivos
    var formData = new FormData();
    formData.append('conversation_id', actual_conversation_id);
    for (var i = 0; i < files.length; i++) {
        formData.append('file', files[i]);
    }

    // Desactivar el formulario
    $('#upload-form').prop('disabled', true);
    
    // Enviar la solicitud AJAX para cargar los archivos
    $.ajax({
        type: 'POST',
        url: '/agente_licitaciones/load_files_rag',
        data: formData,
        processData: false,
        contentType: false,
        success: function() {
            console.log("Archivos cargados correctamente.");
        },
        error: function() {
            console.log("Error al cargar los archivos.");
        },
        complete: function() {
            // Reactivar el formulario después de completar la solicitud AJAX
            $('#upload-form').prop('disabled', false);
            
            // Limpiar el campo de selección de archivos
            $('#file').val('');
        }
    });
}
  
  function getConversation(conversationId, userAvatar, botAvatar) {
    $.ajax({
      type: 'GET',
      url: '/agente_licitaciones/get_conversation/' + conversationId,
      success: function(data) {
        // Se limpia la conversación actual y se obtiene el identificador de la conversación seleccionada
        $("#list-group").empty();
        $('#list-group').data('conversation-id', conversationId);
  
        // Se obtienen los mensajes de la BD y se guardan en un arreglo
        const jsonArray = JSON.parse(data);
  
        // Para cada mensaje se identifica el rol (usuario o agente)
        jsonArray.forEach(function(message) {
          if (message.role == 'user') {
            let user_message = '';
  
            // Se crea el componente HTML que contiene un mensaje del usuario
            user_message += `
              <div class="list-group-item list-group-item-action d-flex gap-3 pt-4">
                <img src="${userAvatar}" alt="user" width="32" height="32" class="rounded-circle">
                <div">
                  <h6>Tú</h6>
                  <div>
                    <p class="opacity-75">
                      <md-block>${message.content}</md-block>
                    </p>
                  </div>
                </div>
              </div>
              `;
            
            // Se añade el mensaje la venta de la conversación
            $("#list-group").append(user_message);
          }
          else if (message.role == 'assistant') {
            let assistant_message = '';
            
            // Se crea el componente HTML que contiene una respuesta del agente
            assistant_message += `
              <div class="list-group-item list-group-item-action d-flex gap-3 pt-4">
                <img src="${botAvatar}" alt="bot" width="32" height="32" class="rounded-circle">
                <div>
                  <h6>Agente</h6>
                  <div>
                    <p>
                      <md-block>${message.content}</md-block>
                    </p>
                  </div>
                </div>
              </div>
              `;
  
            // Se añade la respuesta la venta de la conversación
            $("#list-group").append(assistant_message);
          }
        });
        console.log("¡Conversación cargada!");
      },
      error: function() {
        console.log("Error al obtener conversación.");
      }
    });
  }
  