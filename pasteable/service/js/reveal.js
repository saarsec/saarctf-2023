/**
 * Decrypts information with entered password.
 * Additionally, it will check if delivered hash is the same
 * like the encrypted hash from database.
 * Function will not fail in case of wrong information.
 *
 * @param e
 * @param h_cipher
 * @param t_cipher
 * @param c_cipher
 * @param checksum
 */
function decryptInformation(e, h_cipher, t_cipher, c_cipher, checksum) {
    $('#pass_enter').modal("hide");
    $.ajax({
        url: '../func/paste.php',
        type: 'POST',
        data: {"cipher": h_cipher, "cipher_pass": $('#password').val()},
        success: function(result) {
            let hash = result;
            $('#submitbtn').removeAttr("disabled");
            if(hash !== checksum) {
                showError("Warning: Message Integrity cannot be confirmed!");
            }
            $.ajax({
                url: '../func/paste.php',
                type: 'POST',
                data: {"cipher": t_cipher, "cipher_pass": $('#password').val()},
                success: function(result) {
                    let title = result;
                    $('#title').html(title);
                    $.ajax({
                        url: '../func/paste.php',
                        type: 'POST',
                        data: {"cipher": c_cipher, "cipher_pass": $('#password').val()},
                        success: function(result) {
                            let content = result;
                            $('#contentarea').val(content);
                        },
                        error: function() {
                            showError("Something went wrong!");
                        }
                    });
                },
                error: function() {
                    showError("Something went wrong!");
                }
            });
        },
        error: function() {
            showError("Something went wrong!");
        }
    });
}