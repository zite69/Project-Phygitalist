(function() {
    document.addEventListener('DOMContentLoaded', eventDom => {
        const approve = document.getElementById("btn-id-approve");
        const reject = document.getElementById("btn-id-reject");
        const rejectReason = document.getElementById("id_approval_notes");
        const registration = JSON.parse(JSON.parse(document.getElementById("registration").textContent))[0];
        // const continue = document.querySelector("button[name='_continue']");
        const continueBtn = document.querySelector("button[name=_continue]");
        const approved = document.getElementById("id_approved");
        const action = document.getElementById("id_action");

        approve.addEventListener('click', evtClick => {
            const signature_verified = document.getElementById("id_signature_file_verified").checked;
            let gstpan_verified = false;
            if (registration.gst_status == 'Y') {
                gstpan_verified = document.getElementById("id_gstin_file_verified").checked;
            } else {
                gstpan_verified = document.getElementById("id_pan_file_verified").checked;
            }
            if (!(signature_verified && gstpan_verified)) {
                let msg = "You must verify the signature file and the ";
                if (registration.gst_status == 'Y')
                    msg += "GST scan upload file";
                else
                    msg += "PAN scan upload file";
                alert(msg);
                return;
            }
            action.value = "approved";
            approved.checked = true;
            continueBtn.click();
        });
        reject.addEventListener('click', evtClick => {
            if (rejectReason.value.trim() == "") {
                alert('You must specify a reason for Rejection');
                return;
            }
            action.value = "rejected";
            approved.checked = false;
            continueBtn.click();
        });
    });
})();
