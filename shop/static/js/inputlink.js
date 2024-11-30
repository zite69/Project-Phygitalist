(function () {
  // console.log("inside inputlink.js");
  function validatePhone(phone) {
      //const regex = /^(?:(?:\+|0{0,2}91)\s*|0)?\s*(?:[6-9]\d{4})\s*\d{5}$/;
      const regex1 = /^(?:(?:\+|0{0,2})91(\s*|[\-])?|[0]?)?([6789]\d{2}([ -]?)\d{3}([ -]?)\d{4})$/;
      const regex2 = /^(?:(?:\+|0{0,2})91(\s*|[\-])?|[0]?)?([6789]\d{4}([ -]?)\d{5})$/;

      return regex1.test(phone) || regex2.test(phone);
      //looks for numbers like +919923412345 +91 99123 12345 +91 991 231 2345 or 09941212345 or 99123 12345
      // ^: Start of the string.
      // (?:(?:\+|0{0,2}91)\s*|0)?: Optional country code:
      //     (?:\+|0{0,2}91): Matches +91, 091, or 91.
      //     \s*: Optional whitespace.
      //     |0: Or, just a 0.
      // (?:[6-9]\d{2}): The first digit must be 6-9, followed by two more digits.
      // \s*: Optional whitespace.
      // \d{6}: Six more digits.
      // $: End of the string.
  }

  function validateEmail(email) {
    const regex = /^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
    return regex.test(email);
  }

  async function getCode(type, uri, data) {
    const csrf = document.querySelector("input[name='csrfmiddlewaretoken']").value;
    const postdata = { }
    if (type == "phone")
      postdata['phone'] = data;
    else if (type == 'email')
      postdata['email'] = data;

    const resp = await fetch(uri, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf
      },
      body: JSON.stringify(postdata)
    });

    if (!resp.ok) {
      throw new Error("Server communication failed");
    }

    const result = await resp.json();
    return result;
  };

  async function validateAndGetCode(type, getCodeUri, data, link) {
    const errorSpan = document.querySelector(`span.${type}.error`);
    if (errorSpan)
      errorSpan.remove();
    if ((type == 'phone' && validatePhone(data)) || (type == 'email' && validateEmail(data))) {
      console.log(`Got a valid ${type} we are requesting OTP`);
      const resp = await getCode(type, getCodeUri, data);
      console.log("Got response from server:");
      console.log(resp);
      setTimeout(() => {
        console.log("Enabling resend code link");
        link.dataset.status = "init";
        const resendSpan = document.createElement("span");
        resendSpan.innerHTML = '<button class="btn btn-link">Resend Code</button>';
        resendSpan.addEventListener('click', (evt) => {
          console.log("Resend code clicked");
          if (link.dataset.status == 'processing')
            return;
          const resp = validateAndGetCode(type, getCodeUri, data, link);
          handleEntryError(resp, type);
          link.dataset.status = 'processing';
        });
        const step = document.querySelector("#seller-registration").dataset.step;
        const otpDiv = document.querySelector(`#id_${step}-${type}_otp`);
        document.querySelector(".registration-form").insertAdjacentElement('beforeend', resendSpan);
      }, 60 * 1 * 1000);
      return resp;
    } else {
      const errorSpanNew = document.createElement("span");
      errorSpanNew.textContent = `${type} is invalid, please check it`;
      errorSpanNew.classList.add("error", type);
      link.classList.add("error");
      link.parentNode.insertBefore(errorSpanNew, link);
      return null;
    }
  };

  function handleEntryError(response, type) {
    for (const es of document.querySelectorAll("span.error.form")) {
      es.remove();
    }
    if (response.error) {
      const errorSpan = document.createElement("span");
      errorSpan.textContent = response.error;
      errorSpan.classList.add("error", "form");
      document.querySelector(".registration-form").insertBefore(errorSpan, document.querySelector("form"));
    } else {
      const errorSpan = document.querySelector("span.form.error");
      const enterOtpOld = document.querySelector("span.enterotp");
      if (errorSpan)
        errorSpan.remove();
      if (enterOtpOld)
        enterOtpOld.remove();
      const enterOtpSpan = document.createElement("span");
      enterOtpSpan.textContent = `Please enter the OTP received on your ${type}`
      enterOtpSpan.classList.add("enterotp", type);
      const step = document.querySelector("#seller-registration").dataset.step;
      const otpDiv = document.querySelector(`#id_${step}-${type}_otp`);
      document.querySelector(".registration-form").insertBefore(enterOtpSpan, otpDiv);
    }
  }

  function handleValidateError(response, type) {
    for (const es of document.querySelectorAll("span.enterotp")) {
      es.remove();
    }
    if (response.error) {
      const errorSpan = document.createElement("span");
      errorSpan.textContent = response.error;
      errorSpan.classList.add("error", "form");
      const form = document.querySelector("#seller-registration");
      const otpDiv = document.querySelector(`#id_${form.dataset.step}-${type}_otp`);
      document.querySelector(".registration-form").insertBefore(errorSpan, otpDiv);
    } else {

    }
  }

  document.addEventListener('DOMContentLoaded', (eventLoaded) => {
    // console.log("Inside DOMContentLoaded");
    const inputLinks = document.getElementsByClassName("input-link");
    for (const link of inputLinks) {
      const input = link.querySelector("input");
      const getcode = link.querySelector("button.get-link");
      const type = link.dataset.type;
      // const widgetType = link.dataset.typeWidget;
      const getCodeUri = link.dataset.getCodeUri;
      // console.log(input);
      // console.log(getcode);
      // console.log(type);
      getcode.addEventListener('click', async (eventClick) => {
        if (link.dataset.status == 'processing') {
          return;
        }
        const resp = await validateAndGetCode(type, getCodeUri, input.value, link);
        handleEntryError(resp, type);
        if (resp != null && !resp.error)
          link.dataset.status = 'processing';
        // const resp = await validateOtp(type, getCodeUri, input.value, link);
        // handleValidateError(resp, type);
      });
      input.addEventListener('keydown', async (eventKey) => {
        // console.log('Input keydown event:');
        // console.log(eventKey);
        if (eventKey.key.toLowerCase() == 'enter') {
          if (link.dataset.status == 'processing'){
            eventKey.preventDefault();
            return;
          }
          const resp = await validateAndGetCode(type, getCodeUri, input.value, link);
          handleEntryError(resp, type);
          if (resp != null && !resp.error)
            link.dataset.status = 'processing';
          // const resp = await validateOtp(type, getCodeUri, input.value, link);
          // handleValidateError(resp, type);
          eventKey.preventDefault();
        }
      })
    }
  });
})();
