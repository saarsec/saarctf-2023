/**
 * Shows and automatically hides
 * Error-Panels
 *
 * @param {string} msg
 * @param {string} id
 */

function showError(msg, id=null) {
    let error_field = document.getElementById("error" + ((id !== null) ? "-" + id : ""));
    $(error_field).removeClass("hidden");
    error_field.style.display = "block";

    let error_msg = document.getElementById("error_message" + ((id !== null) ? "-" + id : ""));
    error_msg.innerHTML = msg;
    setTimeout(function() {
        $(error_field).fadeOut().promise().done(function() {
            $(error_field).addClass("hidden");
        });
    }, 3000);
}

/**
 * Shows and automatically hides
 * Success-Panels
 *
 * @param {string} msg
 * @param {string} id
 */
function showSuccess(msg, id=null) {
    let succ_field = document.getElementById("success" + ((id !== null) ? "-" + id : ""));
    $(succ_field).removeClass("hidden");
    succ_field.style.display = "block";
    
    let succ_msg = document.getElementById("success_message" + ((id !== null) ? "-" + id : ""));
    succ_msg.innerHTML = msg;
    setTimeout(function() {
        $(succ_field).fadeOut().promise().done(function() {
            $(succ_field).addClass("hidden");
        });
    }, 3000);
}