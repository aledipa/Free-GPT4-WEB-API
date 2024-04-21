// Turns on the button
function turnOn(id_on, id_off, set) {
    document.getElementById(id_off).style.color = "#C8D9DE";
    document.getElementById(id_on).style.color = "#035306";
    document.getElementById(set).style.color = "#035306";
}

// Turns off the button
function turnOff(id_on, id_off, set) {
    document.getElementById(id_off).style.color = "#8B0000";
    document.getElementById(id_on).style.color = "#C8D9DE";
    document.getElementById(set).style.color = "#8B0000";
}

// Changes the button text and color
function changeButton(button_id) {
    document.getElementById(button_id).style.backgroundColor = "#035306";
    document.getElementById(button_id).textContent = "Change";
}

// Hides an element and shows another
function replaceElement(id_to_hide, id_to_show) {
    document.getElementById(id_to_hide).hidden = true;
    document.getElementById(id_to_show).hidden = false;
}

// Shows an element
function showElement(id_to_show) {
    document.getElementById(id_to_show).hidden = false;
}

// Hides an element
function hideElement(id_to_hide) {
    document.getElementById(id_to_hide).hidden = true;
}

// Gets available models for choosen A.I. Provider
$(document).ready(function(){
    $("#provider").change(function(){
      var inputValue = $(this).val();
      $.ajax({
        url: '/models',
        data: {
          'provider': inputValue
        },
        success: function(response) {
            var select = document.getElementById("model");

            // Remove existing models
            while (select.firstChild) {
                select.removeChild(select.firstChild);
            }

            // Add the new models
            for (var i=0; i<response.length; i++) {
                var option = document.createElement("option");
                option.innerText = response[i];
                option.value = response[i];
                select.add(option);
            }
        }
      });
    });
  }); 