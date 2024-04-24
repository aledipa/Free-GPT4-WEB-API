// Turns on the button
function turnOn(idOn, idOff, set) {
    document.getElementById(idOff).style.color = "#C8D9DE";
    document.getElementById(idOn).style.color = "#035306";
    document.getElementById(set).style.color = "#035306";
}

// Turns off the button
function turnOff(idOn, idOff, set) {
    document.getElementById(idOff).style.color = "#8B0000";
    document.getElementById(idOn).style.color = "#C8D9DE";
    document.getElementById(set).style.color = "#8B0000";
}

// Changes the button text and color
function changeButton(buttonID) {
    document.getElementById(buttonID).style.backgroundColor = "#035306";
    document.getElementById(buttonID).textContent = "Change";
}

// Hides an element and shows another
function replaceElement(idToHide, idToShow) {
    document.getElementById(idToHide).hidden = true;
    document.getElementById(idToShow).hidden = false;
}

// Shows an element
function showElement(idToShow) {
    element = document.getElementById(idToShow);
    element.hidden = false;
    element.classList.remove('hidden');
}

// Hides an element
function hideElement(idToHide) {
    element = document.getElementById(idToHide);
    element.hidden = true;
    element.classList.add('hidden');
}

// Copies the text in the given id to the clipboard
function copyTextToClipboardFromName(name) {
    var copyText = document.getElementsByName(name)[0].value
    navigator.clipboard.writeText(copyText);
}

// Replaces the element in the given ID with the given text
function replaceElementWithText(id, text) {
    var element = document.getElementById(id);
    var originalElement = element;
    // Creates a new element
    var newElement = document.createElement('p');
    // Adds some content to the new element
    newElement.textContent = text;
    newElement.classList.add('darkblue');
    newElement.classList.add('inline-block');
    newElement.id = id;
    // Replaces the old element with the new one
    element.parentNode.replaceChild(newElement, element);

    return originalElement;
}

function copy(name, id, text) { 
    copyTextToClipboardFromName(name);
    var oldElement = replaceElementWithText(id, text);
    setTimeout((param) => {
        var textElement = document.getElementById(id);
        textElement.parentNode.replaceChild(param, textElement);
    }, 2000, oldElement);
}

function createToken(targetID) {
    $.ajax({
        url: '/generatetoken',
        data: {},
        success: function(response) {
            var tokenText = document.getElementById(targetID).innerText;
            if (tokenText.length == 0) {
                document.getElementById(targetID).innerText = response;
                document.getElementById('token').value = response;
            }
        }
    });

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