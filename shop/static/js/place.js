(function () {
  document.addEventListener('DOMContentLoaded', eventDoc =>{
    const pincode = document.querySelector(".registration-form input.form-control");
    const place = document.querySelector(".registration-form select");
    const uri = pincode.dataset.autocompleteUri;
    console.log(uri);
    console.log(pincode);
    console.log(place);
    $(pincode).autocomplete({
      source: uri,
      minLength: 3,
      select: async function (event, ui) {
        const resp = await fetch(`${uri}?term=${ui.item.value}&action=place`, {
          method: 'GET',
          headers: {
            "Content-Type": "application/json"
          }
        });
        console.log(resp);
        const results = await resp.json();
        place.innerHTML = '';
        results.forEach(option => {
          console.log(option);
          const optionEl = document.createElement("option");
          optionEl.value = option['id'];
          optionEl.text = option['place'];
          console.log(optionEl);
          place.appendChild(optionEl);
        })
      }
    })
  })
})();
