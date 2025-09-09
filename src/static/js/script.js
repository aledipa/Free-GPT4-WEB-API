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
  document.getElementById(idToHide).classList.add("hidden");
  document.getElementById(idToShow).classList.remove("hidden");
}

// Shows an element
function showElement(idToShow) {
  element = document.getElementById(idToShow);
  element.classList.remove("hidden");
}

// Hides an element
function hideElement(idToHide) {
  element = document.getElementById(idToHide);
  element.classList.add("hidden");
}

// Shows multiple elements
function showElementClass(classToShow) {
  elements = document.getElementsByClassName(classToShow);
  for (var i=0; i<elements.length; i++) {
    elements[i].classList.remove("hidden");
  }
}

// Hides multiple elements
function hideElementClass(classToHide) {
  elements = document.getElementsByClassName(classToHide);
  for (var i=0; i<elements.length; i++) {
    elements[i].classList.add("hidden");
  }
}

// Hides a composed warning
function hideWarning(idToHide) {
  document.getElementById(idToHide).classList.add("hidden");
}

// Shows a composed warning
function showWarning(idToShow) {
  document.getElementById(idToShow).classList.remove("hidden");
}

// Enables the input
function enableEditing(idToEnable) {
  document.getElementById(idToEnable).removeAttribute("readonly");
}

// Disables the input
function disableEditing(idToDisable) {
  document.getElementById(idToDisable).setAttribute("readonly", true);
}

// Copies the text in the given id to the clipboard
function copyTextToClipboardFromName(name) {
  var copyText = document.getElementsByName(name)[0].value;
  navigator.clipboard.writeText(copyText);
}

// Replaces the element in the given ID with the given text
function replaceElementWithText(id, text) {
  var element = document.getElementById(id);
  var originalElement = element;
  // Creates a new element
  var newElement = document.createElement("p");
  // Adds some content to the new element
  newElement.textContent = text;
  newElement.classList.add("darkblue");
  newElement.classList.add("inline-block");
  newElement.id = id;
  // Replaces the old element with the new one
  element.parentNode.replaceChild(newElement, element);

  return originalElement;
}

function copy(name, id, text) {
  copyTextToClipboardFromName(name);
  var oldElement = replaceElementWithText(id, text);
  setTimeout(
    (param) => {
      var textElement = document.getElementById(id);
      textElement.parentNode.replaceChild(param, textElement);
    },
    2000,
    oldElement,
  );
}

function createToken(targetID) {
  $.ajax({
    url: "/generatetoken",
    data: {},
    success: function (response) {
      var tokenText = document.getElementById(targetID).innerText;
      if (tokenText.length == 0) {
        document.getElementById(targetID).innerText = response;
        document.getElementById("token").value = response;
      }
    },
  });
}

function addProxy() {
  // Gets the number of proxy input fields in 'proxy_list_div'
  var proxyListDiv = document.getElementById("proxy_list_div");
  var proxyList = proxyListDiv.getElementsByTagName("input");

  // Checks if there's already an empty proxy input field
  for (var i = 0; i < proxyList.length; i++) {
    if (proxyList[i].value.length == 0) {
      return;
    }
  }

  // adds a new proxy input field
  var newProxyDiv = document.createElement("div");
  newProxyDiv.classList.add("flex", "justify-start", "mb-3");

  var newProxy = document.createElement("input");
  newProxy.type = "text";
  newProxy.name = "proxy_" + (proxyList.length + 1);
  newProxy.id = newProxy.name;
  newProxy.classList.add(
    "input",
    "outline-none",
    "py-1",
    "px-2",
    "rounded-lg",
    "inter",
    "w-full",
  );
  newProxy.placeholder = "protocol://user:password@host:port";
  newProxy.setAttribute("onchange", "checkAllProxies()");
  newProxyDiv.appendChild(newProxy);

  // adds the 'delete' image button to the new proxy input field
  var deleteButton = document.createElement("img");
  deleteButton.src = "static/img/delete(Anggara).png";
  deleteButton.classList.add(
    "inline-block",
    "mx-2",
    "p-1",
    "hover:brightness-125",
  );
  deleteButton.width = 32;
  deleteButton.onclick = function () {
    newProxyDiv.remove();
  };
  newProxyDiv.appendChild(deleteButton);

  document.getElementById("proxy_list_div").appendChild(newProxyDiv);
}

function deleteElement(id) {
  document.getElementById(id).remove();
}

// Checks if the proxy syntax is correct
function checkProxySyntax(proxy) {
  var proxyRegex =
    /^((http|https|socks4|socks5):\/\/)?([a-zA-Z0-9]+:[a-zA-Z0-9]+@)?([a-zA-Z0-9.-]+):([0-9]+)$/;
  return proxyRegex.test(proxy);
}

// Warns the user if the proxy syntax is incorrect
function warnProxySyntax(proxy, proxyID) {
  if (checkProxySyntax(proxy)) {
    document
      .getElementById(proxyID)
      .classList.remove("border_red", "label_red", "lightpink_bg");
  } else {
    document
      .getElementById(proxyID)
      .classList.add("border_red", "border", "label_red", "lightpink_bg");
  }
}

// Checks the syntax at every proxy input field at input change
function checkAllProxies() {
  var proxyListDiv = document.getElementById("proxy_list_div");
  var proxyList = proxyListDiv.getElementsByTagName("input");
  for (var i = 0; i < proxyList.length; i++) {
    warnProxySyntax(proxyList[i].value, proxyList[i].id);
  }
}

// Validates password length (minimum 8 characters)
function validatePasswordLength() {
  var newPassword = document.getElementById("new_password").value;
  var confirmPassword = document.getElementById("confirm_password").value;
  
  // Check if either password field is not empty and has less than 8 characters
  if ((newPassword.length > 0 && newPassword.length < 8) || 
      (confirmPassword.length > 0 && confirmPassword.length < 8)) {
    showElement("error_password_length");
    hideElement("error_password");
    hideElement("success_password");
    return false;
  } else {
    hideElement("error_password_length");
    // Only validate match if both fields have valid length
    if (newPassword.length >= 8 && confirmPassword.length >= 8) {
      return validatePasswordMatch();
    }
    return true;
  }
}

// Checks if new password and confirm password match (internal function)
function validatePasswordMatch() {
  var newPassword = document.getElementById("new_password").value;
  var confirmPassword = document.getElementById("confirm_password").value;
  
  if (newPassword == confirmPassword) {
    hideElement("error_password");
    hideElement("error_password_length");
    showElement("success_password");
    return true;
  } else {
    hideElement("success_password");
    hideElement("error_password_length");
    showElement("error_password");
    return false;
  }
}

// Checks if new password and confirm password match (main function for compatibility)
function checkPasswordMatch() {
  var newPassword = document.getElementById("new_password").value;
  var confirmPassword = document.getElementById("confirm_password").value;
  
  // Check length first
  if ((newPassword.length > 0 && newPassword.length < 8) || 
      (confirmPassword.length > 0 && confirmPassword.length < 8)) {
    showElement("error_password_length");
    hideElement("error_password");
    hideElement("success_password");
    return false;
  }
  
  // Hide length error if length is valid
  hideElement("error_password_length");
  
  // Check match if both passwords have content
  if (newPassword.length > 0 && confirmPassword.length > 0) {
    return validatePasswordMatch();
  }
  
  // If passwords are empty, hide all messages
  if (newPassword.length === 0 && confirmPassword.length === 0) {
    hideElement("error_password");
    hideElement("error_password_length");
    hideElement("success_password");
  }
  
  return newPassword.length >= 8 && confirmPassword.length >= 8;
}

// Opens the update password form
function openPasswordUpdate() {
  replaceElement("open_password_update", "cancel_password_update");
  showElement("password_update");
}

// Closes the update password form
function cancelPasswordUpdate() {
  hideElement("password_update");
  hideElement("success_password");
  hideElement("error_password");
  hideElement("error_password_length");
  replaceElement("cancel_password_update", "open_password_update");
  document.getElementById("new_password").value = "";
  document.getElementById("confirm_password").value = "";
}

// Enables the save button if the password is correct
function enableSaveButton() {
  var pass_length = document.getElementById("password").value.length;
  var isPasswordUpdateClosed = document.getElementById("password_update").classList.contains("hidden");
  var isPasswordValid = isPasswordUpdateClosed || checkPasswordMatch();
  
  if (isPasswordValid && pass_length > 0) {
    replaceElement('save_label_dummy', 'save_label');
  } else {
    replaceElement('save_label', 'save_label_dummy');
  }
}

async function fetchToken() {
  try {
      const response = await fetch("/generatetoken");
      const uuid = await response.text();
      // console.log("Stored UUID:", uuid);
      return uuid;
  } catch (error) {
      console.error("Error fetching token:", error);
  }
}

// Adds a new user to the list
async function addUser(inputId) {
  const input = document.getElementById(inputId);
  const username = input.value.trim();

  if (!username) {
      alert('Please enter a username');
      return;
  }

  (async () => {
      const uuid = await fetchToken();
      console.log("Token ready for use:", uuid);

      const newRowHtml = `
      <tr id="user_${uuid}" class="user">
          <td class="py-1 fond-bold inter darkblue text-lg border-b border-slate-800">
              <div>
                  <div class="flex justify-start mb-3">
                      <img id="delete_icon" src="/static/img/delete(Anggara).png" width="32" class="inline-block mx-2 p-0.5 hover:brightness-125" alt="Delete" onclick="deleteElement('user_${uuid}');"/>
                      <input type="text" id="username_${uuid}" name="username_${uuid}" class="input outline-none py-1 px-2 rounded-lg inter" placeholder="username_${uuid}" value="${username}" onchange="showElement('ELEMENT')" readonly>
                  </div>
              </div>
          </td>
          <td class="py-1 fond-bold inter darkblue text-lg align-top">
              <button type="button" id="edit_user_${uuid}" class="text-white darkblue_bg outline-none focus:outline-none inter rounded-lg text-md px-4 py-1 text-center inline-flex items-center me-2 hover:opacity-95" onclick="enableEditing('username_${uuid}'); replaceElement(this.id, 'confirm_user_${uuid}'); focusOnInput('username_${uuid}')">
                  <img src="/static/img/edit(PixelPerfect).png" class="w-3.5 h-3.5 me-2"/>
                  <b>Edit</b>
              </button>
              <button type="button" id="confirm_user_${uuid}" class="text-white darkgreen_bg outline-none focus:outline-none inter rounded-lg text-md px-4 py-1 text-center inline-flex items-center me-2 hover:opacity-95 hidden" onclick="disableEditing('username_${uuid}'); replaceElement(this.id, 'edit_user_${uuid}')">
                  <img src="/static/img/check(iconmasadepan).png" class="w-3.5 h-3.5 me-2"/>
                  <b>Confirm</b>
              </button>
          </td>
      </tr>
      `;

      const addUserRow = document.querySelector('tr.user');
      addUserRow.insertAdjacentHTML('afterend', newRowHtml);

      input.value = '';
  })();
}

// Focusses on an input

function focusOnInput(inputId) {
  const inputElement = document.getElementById(inputId);
  if (inputElement) {
      inputElement.focus(); // Focus on the input
      const length = inputElement.value.length; // Get the length of the input's value
      inputElement.setSelectionRange(length, length); // Set cursor position to the end
  } else {
      console.error(`Element with ID "${inputId}" not found.`);
  }
}

// Gets available models for chosen A.I. Provider
$(document).ready(function () {
  $("#provider").change(function () {
    var inputValue = $(this).val();
    $.ajax({
      url: "/models",
      data: {
        provider: inputValue,
      },
      success: function (response) {
        var select = document.getElementById("model");

        // Remove existing models
        while (select.firstChild) {
          select.removeChild(select.firstChild);
        }

        // Add the new models
        for (var i = 0; i < response.length; i++) {
          var option = document.createElement("option");
          option.innerText = response[i];
          option.value = response[i];
          select.add(option);
        }
      },
    });
  });

  // updateUsernameIds();
});
