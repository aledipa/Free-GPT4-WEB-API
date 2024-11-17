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
}

// Hides an element
function hideElement(idToHide) {
  element = document.getElementById(idToHide);
  element.hidden = true;
}

// Hides a composed warning
function hideWarning(idToHide) {
  document.getElementById(idToHide).classList.add("hidden");
}

// Shows a composed warning
function showWarning(idToShow) {
  document.getElementById(idToShow).classList.remove("hidden");
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

// Checks if new password and confirm password match
function checkPasswordMatch() {
  var newPassword = document.getElementById("new_password").value;
  var confirmPassword = document.getElementById("confirm_password").value;
  if (newPassword == confirmPassword) {
    if (newPassword.length > 0) {
      replaceElement("error_password", "success_password");
      return true;
    }
  } else {
    replaceElement("success_password", "error_password");
  }
  return false;
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
  replaceElement("cancel_password_update", "open_password_update");
  document.getElementById("new_password").value = "";
  document.getElementById("confirm_password").value = "";
}

// Enables the save button if the password is correct
function enableSaveButton() {
  var pass_length = document.getElementById("password").value.length;
  var isPasswordUpdateClosed = document.getElementById("password_update").hidden;
  if ((checkPasswordMatch() || isPasswordUpdateClosed) && pass_length > 0) {
    replaceElement('save_label_dummy', 'save_label');
  } else {
    replaceElement('save_label', 'save_label_dummy');
  }
}

// Gets available models for choosen A.I. Provider
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
});
