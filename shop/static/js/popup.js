// Function to show and hide popups
function showPopup(popupId) {
    document.getElementById(popupId).style.display = "flex";
}

function closePopup(popupId) {
    document.getElementById(popupId).style.display = "none";
}

// Show the "Create your free seller account" popup when any play button is clicked
document.querySelectorAll('.play_button').forEach(button => {
    button.onclick = function() {
        showPopup("popupBox");
    };
});

// Close the "Create your free seller account" popup
document.getElementById("okBtn").onclick = function() {
    closePopup("popupBox");
};

// Show the "How We Ensure 10X Sales?" popup when the specific link is clicked
document.getElementById("playSales").onclick = function() {
    showPopup("salesPopupBox");
};

// Close the "How We Ensure 10X Sales?" popup
document.getElementById("salesOkBtn").onclick = function() {
    closePopup("salesPopupBox");
};

// Add event listeners for "Join Seller School" and "Gross Margin Calculator"
document.getElementById("playSchool").onclick = function() {
    showPopup("salesPopupBox");
};

document.getElementById("playMargin").onclick = function() {
    showPopup("salesPopupBox");
};

// Close the popup if the user clicks outside the popup content
window.onclick = function(event) {
    const popup1 = document.getElementById("popupBox");
    const popup2 = document.getElementById("salesPopupBox");
    if (event.target === popup1) {
        closePopup("popupBox");
    } else if (event.target === popup2) {
        closePopup("salesPopupBox");
    }
};
