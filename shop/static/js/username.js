(function () {
  async function validateUsername(url, user) {
    console.log("validateUsername being called");
    //console.trace("We have been called by");
    const csrf = document.querySelector("input[name='csrfmiddlewaretoken']").value;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf
      },
      body: JSON.stringify({ "username": user, "csrfmiddlewaretoken": csrf })
    });
    if (!response.ok) {
      console.log(`Response was not ok ${response}`);
    }
    const result = await response.json();
    return result;
  }

  document.addEventListener('DOMContentLoaded', (docEvent) => {
    const username = document.querySelector(".username");
    //console.log("inside on domcontentloaded");
    function resetUsername(event) {
      console.log("Being fired in reset username");
      username.dataset.action = 'none';
      username.classList.remove('error');
      username.classList.remove('success');
      const errorCheck =  document.querySelector("span.username.error");
      if (errorCheck)
        errorCheck.remove();
    }
    username.addEventListener('click', resetUsername);
    username.addEventListener('focus', resetUsername);
    username.addEventListener('focusout', async (event) => {
      console.log("focus out on username");
      const action = username.dataset.action;
      console.log(action);
      if (action == 'none') {
        console.log("we are none");
        username.dataset.action = 'checking';
      } else {
        console.log("we are not none");
        return;
      }
      const uri = username.dataset.validate;
      const user = username.value;
      console.log("username focusout");
      const usernameStatus = await validateUsername(uri, user);
      console.log(usernameStatus);
      if (usernameStatus.status == 'unavailable') {
        const errorSpan = document.createElement("span");
        errorSpan.textContent = "Username is not available please choose another name";
        errorSpan.classList.add("error", "username");
        username.classList.add("error");
        username.parentNode.insertBefore(errorSpan, username);
      } else if (usernameStatus.status == 'available') {
        const errorSpan = document.querySelector("span.username.error");
        if (errorSpan)
          errorSpan.remove();
        username.classList.remove("error");
        username.classList.remove("is-invalid"); //in case it has been submitted to the server and come back and invalid
        username.classList.add("success");
        //in case it has come back from the server and has errors
        const errorUser = document.querySelector("#error_1_id_0-username");
        if (errorUser != undefined )
          Array.from(errorUser.children).forEach((el) => el.remove());
        //username.setAttribute('readonly', true);
      }
    });
  });
})();
