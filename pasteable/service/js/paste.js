/**
 * Handles requests to paste.php etc
 */
function submitPaste() {
    let form = $('#pasteform')[0];
    if(!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
    }

    if($('#submitbtn').html() === "Save Changes") {
        $.post('../../func/paste.php', {update_id: $('#id').val(), update_content: $('#contentarea').val(), update_title: $('#title').val(), update_pass: "<?php if($EDIT_MODE) echo $retrieved_data[2]; ?>"})
            .done(function(response) {
                if(response === "success") {
                    showSuccess("Paste was successfully updated!");
                } else {
                    showError("Paste Update has failed!");
                }
            })
            .fail(function(xhr, status, error) {
                showError("Paste Update has failed!");
            });
        return;
    }

    $.post('../../func/paste.php', $('#pasteform').serialize())
        .done(function(response) {
            if(response === "success") {
                showSuccess("Paste was successfully created!");
            } else {
                showError("Paste Creation has failed!");
            }
        })
        .fail(function(xhr, status, error) {
            showError("Paste Creation has failed!");
        });
}