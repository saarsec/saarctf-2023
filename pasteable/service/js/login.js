/**
 * Validates entered input
 *
 * @param input
 * @returns {boolean}
 */
function validateUsername(input) {
    if(!input || input === "" || input === undefined || input === null) {
        showError("Invalid Username");
        return false;
    }
    return true;
}

/**
 * Validates entered input
 *
 * @param input
 * @returns {boolean}
 */
function validatePass(input) {
    if(!input || input === "" || input === undefined || input === null) {
        showError("Invalid Password");
        return false;
    }
    return true;
}

/**
 * Handle POST requests to backend
 */
function submitLogin() {

    if(validateUsername($('#username').val()) && validatePass($('#password').val())) {
        let username = $('#username').val();
        let passHash = CryptoJS.SHA256($('#password').val()).toString();
        $.post('../func/challenge.php', {username: username})
            .done(function(challengestr) {
                if (challengestr !== 'ok') {
                    let key = CryptoJS.enc.Hex.parse(passHash);
                    let challenge = CryptoJS.lib.CipherParams.create({
                        ciphertext: CryptoJS.enc.Hex.parse(challengestr),
                        iv: CryptoJS.enc.Hex.parse(passHash.substring(0, 32)),
                        padding: CryptoJS.pad.NoPadding
                    });
                    let solution = "";    
                    try {
                        solution = CryptoJS.AES.decrypt(challenge, key, challenge).toString(CryptoJS.enc.Utf8).trim();
                    } catch (e) {
                        // ignore decoding errors
                    }
                    $.post('../func/login.php', {username: username, solution: solution})
                        .done(function() {
                            window.location.href += "/home";
                        })
                        .fail(function() {
                            showError("Invalid user credentials");
                        });
                }else{
                    $.post('../func/register.php', {username: username, password: passHash})
                        .done(function() {
                            window.location.href += "/home";
                        })
                        .fail(function() {
                            showError("Invalid user credentials");
                        });
                }
            })
            .fail(function() {
                showError("Invalid user credentials");
            });
    }
}
