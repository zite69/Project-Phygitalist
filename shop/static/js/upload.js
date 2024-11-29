(function() {
    document.addEventListener('DOMContentLoaded', function () {
        const form = document.querySelector("form#seller-registration");
        const p = document.querySelector("p.file-size");
        form.addEventListener('submit', function(event) {
            const file = document.querySelector("input[type='file']");
            if (file.files.item(0).size > 5 * 1024 * 1024) {
                console.log("setting file value to null")
                document.querySelector(".iuw-image-preview").innerHTML = "";
                document.querySelector(".iuw-root").classList.add("empty");
                p.classList.add("error");
                event.preventDefault();
                file.dispatchEvent(new Event('change'));
            }
        });
    });
})();
