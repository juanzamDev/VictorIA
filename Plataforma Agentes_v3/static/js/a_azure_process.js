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
  
    // Se invoca el agente con la pregunta y mensajes actuales como parámetros
    $.ajax({
      type: "POST",
      url: "/agente_azure/agente_azure",
      data: {
        'prompt': question,
        'messages': actual_messages
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
        localStorage.setItem('conversationMessages', JSON.stringify(data.azureAPI.Items));
        localStorage.setItem('parameters', JSON.stringify(data.parameters));
        // Se guarda el histórico de la conversación en la BD
        actual_conversation_id = $('#list-group').data('conversation-id');
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
      url: "/agente_azure/save_conversation",
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
  
  function getConversation(conversationId, userAvatar, botAvatar) {
    $.ajax({
      type: 'GET',
      url: '/agente_azure/get_conversation/' + conversationId,
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
  
  function getClient(id) {
    // Get info client by id 
    $.ajax({
      type: 'GET',
      url: '/agente_azure/get_client/' + id,
      success: function(data) {
        const jsonArray = data;
        localStorage.setItem('dataClient', JSON.stringify(jsonArray));
        console.log(jsonArray)
      },
      error: function() {
        console.log("Error al obtener información.");
      }
    });
  }

  function getPdf( ) {
    var conversationMessages = JSON.parse(localStorage.getItem('conversationMessages'));
    var dataClient = JSON.parse(localStorage.getItem('dataClient'));
    var parameters = JSON.parse(localStorage.getItem('parameters'));
    var numObjects = conversationMessages.length;
    var preCot = parameters.prefijo_cotiz
    var codeMachine = []
    for (var i = 1; i <= numObjects; i++) {
      codeMachine.push(i);
    }
    var totalPriceByMonth = 0;
    // console.log(conversationMessages);
    // console.log(dataClient)
    if (conversationMessages && dataClient) {
      // operations discount
      var clientName = dataClient[0].additional_data[0].Nombre_Cliente;
      var city = dataClient[0].additional_data[0].Region;
      var address = dataClient[0].additional_data[0].Direccion;
      var phone = dataClient[0].additional_data[0].Telefeno_Contacto;
      var email = dataClient[0].additional_data[0].Correo;
      var sellerName = dataClient[0].additional_data[0].Nombre_Vendedor;
      var sellerEmail = dataClient[0].additional_data[0].Mail_Ejec;
      var codClient = dataClient[0].additional_data[0].Cod_Cliente;
      var nitClient = dataClient[0].additional_data[0].No_Ident_Fiscal;
      var margin = parseFloat(dataClient[0].MRGEN)/100;
      var serviceName = conversationMessages[0].serviceName;
      var discount = serviceName === 'Virtual Machines' ? parameters.dto_ins_reservada : parameters.dto_otros_azure;
      var insurace = parameters.seguro_cartera
      conversationMessages.forEach(function(message, index) {
        var price = parseFloat(message.retailPrice);
        console.log(price);
        var priceByHour = (price*(1-discount))*(1 + margin)*(1 + insurace);
        console.log(priceByHour);
        var priceByMonth =  priceByHour*720
        console.log(priceByMonth);
        message.codeMachine =  codeMachine[index]
        message.priceByMonth = priceByMonth.toFixed(2);
        message.margin = margin;
        message.client = clientName
        message.city = city
        message.address = address
        message.phone = phone
        message.email = email
        message.trm = ""
        message.seller = sellerName
        message.code = codClient
        message.nit = nitClient
        message.opportunity = ""
        message.sellerEmail = sellerEmail
        message.preCot = preCot
        var date = new Date();
        var effectiveDate = new Date(date);
        effectiveDate.setDate(effectiveDate.getDate() + 30);
        message.date = date.toISOString().slice(0,10);
        message.effectiveDate = effectiveDate.toISOString().slice(0,10);
        totalPriceByMonth += parseFloat(message.priceByMonth);
      });
      // conversationMessages.totalPriceByMonth = totalPriceByMonth.toFixed(2);
      conversationMessages.forEach(function (message) {
        message.totalPriceByMonth = totalPriceByMonth.toFixed(2);
      });
      console.log(conversationMessages)
      $.ajax({
        type: "POST",
        url: "/agente_azure/create_pdf",
        contentType: "application/json",
        data: JSON.stringify({
          'history': conversationMessages
        }),
        success: function() {
          console.log("¡Generación de PDF exitosa!");
        },
        error: function() {
          console.log("error en la generación del PDF");
        }
      });
    } else {
      console.log("No hay conversación o datos del cliente en localStorage.");
    }
  }