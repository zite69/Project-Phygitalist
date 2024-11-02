(function () {
  document.addEventListener('DOMContentLoaded', eventDoc => {
    const step = document.getElementById("seller-registration").dataset.step;
    const divGst = document.getElementById('id-gstin');
    const divPan = document.getElementById('id-pan');
    const initialSelection = document.querySelector(`input[name="${step}-gst_status"]:checked`);
    if (initialSelection.value == 'Y') {
      divGst.classList.remove("hide");
      divPan.classList.add("hide");
    } else {
      divGst.classList.add("hide");
      divPan.classList.remove("hide");
    }

    for (const choice of document.querySelectorAll(`input[name='${step}-gst_status']`)) {
      console.log(choice.attributes['value']);
      choice.addEventListener('click', event => {
        switch (choice.attributes['value'].value) {
          case 'Y':
            divPan.classList.add("hide");
            divGst.classList.remove("hide");
            break;
          default:
            divPan.classList.remove("hide");
            divGst.classList.add("hide");
            break;
        }
      })
    }

    const submit = document.getElementById("submit-gst");
    submit.addEventListener('click', event => {
      const selection = document.querySelector(`input[name="${step}-gst_status"]:checked`);
      console.log(selection);
      if (selection) {
        switch (selection.value) {
          case 'Y':
            if (divGst.querySelector("input").value == "") {
              divGst.classList.remove("success");
              divGst.classList.add("error");
              const errorSpan = document.createElement("span");
              errorSpan.textContent = 'Please enter GST code';
              errorSpan.classList.add("error", "form");
              document.querySelector(".registration-form").insertBefore(errorSpan, document.querySelector(`#div_id_${step}-gstin`));
              event.preventDefault();
            } else {
              divGst.classList.remove("error");
              divGst.classList.add("success");
              document.querySelector("span.form.error")?.remove();
            }
          default:
            if (divPan.querySelector("input").value == "") {
              divPan.classList.remove("success");
              divPan.classList.add("error");
              errorSpan.textContent = 'Please enter PAN number';
              errorSpan.classList.add("error", "form");
              document.querySelector(".registration-form").insertBefore(errorSpan, document.querySelector(`#div_id_${step}-gstin`));
              event.preventDefault();
            } else {
              divPan.classList.remove("error");
              divPan.classList.add("success");
              document.querySelector("span.form.error")?.remove();
            }
        }
      }
    })
  });
})();
