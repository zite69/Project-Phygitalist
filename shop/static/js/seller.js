(function () {
  async function validateUsername(url, user) {
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
    username.addEventListener('focus', (event) => {
      const errorCheck = document.querySelector("span.username.error");
      if (errorCheck)
        errorCheck.remove();
    });
    username.addEventListener('focusout', async (event) => {
      const uri = username.dataset.validate;
      const user = username.value;
      const usernameStatus = await validateUsername(uri, user);
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
        username.classList.add("success");
        username.setAttribute('readonly', true);
      }
    })
  });
})();
