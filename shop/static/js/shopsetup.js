(function () {
  function slugify(str) {
    str = str.replace(/^\s+|\s+$/g, ''); // trim leading/trailing white space
    str = str.toLowerCase(); // convert string to lowercase
    str = str.replace(/[^a-z0-9 -]/g, '') // remove any non-alphanumeric characters
             .replace(/\s+/g, '-') // replace spaces with hyphens
             .replace(/-+/g, '-'); // remove consecutive hyphens
    return str;
  }
  function handleChange(event, handle, short) {
    const newHandle = event.target.value;
    handle.value = slugify(newHandle).slice(0, 20);
    short.value = handle.value.slice(0, 12);
    handle.dataset.editted = true;
  }

  document.addEventListener('DOMContentLoaded', eventDoc => {
    const name = document.getElementById("shop-name");
    const handle = document.getElementById("shop-handle");
    console.log(name);
    console.log(handle);

    name.addEventListener('input', eventInput => {
      const newName = eventInput.target.value;
      if (!handle.dataset.editted) {
        handle.value = slugify(newName).slice(0, 12);
      }
    });

    handle.addEventListener('input', eventInput => {
      handleChange(eventInput, handle, short);
    });

    handle.addEventListener('change', eventInput => {
      handleChange(eventInput, handle, short);
    });
  });
})();
