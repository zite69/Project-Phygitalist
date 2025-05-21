(function() {
    function scrollTo(hash) {
        location.hash = '#' + hash + '-section';
    }

    document.addEventListener('DOMContentLoaded', () => {
        let currentForm = null;

        const pickupPincode = document.getElementById("id_pickup-pincode");
        const pickupPostcode = document.getElementById("id_pickup-postcode");
        pickupPostcode.value = pickupPincode.value;
        const msgDiv = document.querySelector(".alert.alert-success div.alertinner")
        if (msgDiv && msgDiv != undefined) {
            const msgContent = msgDiv.textContent.trim();
            if (msgContent.startsWith("Your pickup address"))
                scrollTo('bank');
            if (msgContent.startsWith("Your bank"))
                scrollTo('seller')
            if (msgContent.startsWith("Your shipping"))
                scrollTo('tnc');
        }
        
        /* Disable the zite69 shipping preference */
        const shippingPref = document.querySelector("#id_seller-shipping_preference_1");
        if (shippingPref && shippingPref != undefined)
            shippingPref.disabled = true;
          // Attach the same focus (or click) listener to every input
          document.querySelectorAll('form input').forEach(inputEl => {
            inputEl.addEventListener('focus', onFocusInput);
            // or inputEl.addEventListener('click', onFocusInput);
          });

          function onFocusInput(evt) {
            const inputEl = evt.target;
            const formEl = inputEl.form;

            // If no form is in "editing mode" yet:
            if (!currentForm) {
              // Set the newly focused form as editing
              currentForm = formEl;
              // Make all other forms readonly
              makeReadonlyAllBut(currentForm.id);
              return;
            }

            // If a form is already in editing mode:
            if (currentForm !== formEl) {
              // The user is trying to edit a different form
              alert("You must save the current form before editing another form.");
              // Optionally, force the blur or restore focus to the original input:
              inputEl.blur();
            }
            // else: If the same form is being focused again, do nothing special.
          }

          // Utility to make all but the given form readonly
          function makeReadonlyAllBut(activeFormId) {
            document.querySelectorAll('form').forEach(form => {
              if (form.id !== activeFormId) {
                // Mark every input in other forms as readonly or disabled
                form.querySelectorAll('input').forEach(inp => {
                  inp.readOnly = true;
                  // If you want file inputs disabled:
                  if (inp.type === 'file') {
                    inp.disabled = true;
                  }
                });
              } else {
                // Make sure the "active" form is editable
                form.querySelectorAll('input').forEach(inp => {
                  inp.readOnly = false;
                  if (inp.type === 'file') {
                    inp.disabled = false;
                  }
                });
              }
            });
          }
          // You will likely also want a "Save" button that resets currentForm to null
          // and re-enables inputs on all forms if you want to allow editing them again.
        }
    );
})();
