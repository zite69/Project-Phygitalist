(function () {
  async function verifyOtp(uri, code) {
    const csrf = document.querySelector("input[name='csrfmiddlewaretoken']").value;
    const postdata = {
      "code": code
    }
    const resp = await fetch(uri, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf
      },
      body: JSON.stringify(postdata)
    });
    if (!resp.ok) {
      console.log(`Error with the response: ${resp}`);
      return { "error": resp.text };
    }
    const result = await resp.json();
    return result;
  }
  document.addEventListener('DOMContentLoaded', eventDom => {

  });
})();
