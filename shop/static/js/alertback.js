(function () {
    history.pushState(null, document.title, location.href);
    document.addEventListener('DOMContentLoaded', eventDom => {
        window.addEventListener('popstate', popEvent => {
            alert("Please do not go back to previous steps. You can edit your information after you complete your registration");
        })
    }) 
})();
