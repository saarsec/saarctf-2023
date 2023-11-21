<?php

/**
 * Paste Library
 *
 * Contains all commonly used functions
 * concerning the pastes
 */

/**
 * Load Pastes as decrypted array
 *
 * @param $APP_SECRET
 * @param $CIPHER_SECRET
 * @param $CIPHER_RING
 * @param $MYSQLI
 * @return array
 */
function loadPastes($APP_SECRET, $CIPHER_SECRET, $CIPHER_RING, $MYSQLI) {
    $ID = $_SESSION['id'];
    $OPTIONS = 0;
    $IV = $APP_SECRET;
    $KEY = $CIPHER_SECRET;
    $stmt = $MYSQLI->prepare("SELECT * FROM user_pastes WHERE paste_author = ?");
    if (
        $stmt &&
        $stmt -> bind_param('s', $ID) &&
        $stmt -> execute()
    ) {
        $result = $stmt->get_result();
        $pastes = array();
        while ($row = $result->fetch_assoc()) {
            $row['paste_title'] = openssl_decrypt($row['paste_title'], $CIPHER_RING, $KEY, $OPTIONS, $IV);
            $row['paste_content'] = openssl_decrypt($row['paste_content'], $CIPHER_RING, $KEY, $OPTIONS, $IV);

            array_push($pastes, $row);
        }

        return $pastes;
    } else {
        // something went wrong...!
        die("ERROR: Could not load pastes!");
    }
}


/**
 * Get editable Paste information for Admin
 * or return simply false
 *
 * @param $ID
 * @param $APP_SECRET
 * @param $CIPHER_SECRET
 * @param $CIPHER_RING
 * @param $MYSQLI
 * @return array|bool
 */
function loadPasteToEdit($ID, $APP_SECRET, $CIPHER_SECRET, $CIPHER_RING, $MYSQLI) {
    $PROVIDED_ID = $MYSQLI->real_escape_string($ID);
    $OPTIONS = 0;
    $IV = $APP_SECRET;
    $KEY = $CIPHER_SECRET;
    $stmt = $MYSQLI->prepare("SELECT paste_title, paste_content, paste_pass, paste_hash FROM user_pastes WHERE paste_id = ?");
    if (
        $stmt &&
        $stmt -> bind_param('s', $PROVIDED_ID) &&
        $stmt -> execute() &&
        $stmt -> store_result() &&
        $stmt -> bind_result($title, $content, $pass, $hash) &&
        $stmt -> fetch()
    ) {
        $title = openssl_decrypt($title, $CIPHER_RING, $KEY, $OPTIONS, $IV);
        $content = openssl_decrypt($content, $CIPHER_RING, $KEY, $OPTIONS, $IV);

        // encrypt data with sha1-hash of password and return
        return [$title, $content, $pass, $hash];
    } else {
        // something went wrong...!
        return false;
    }
}

/**
 * Fetch Paste information for reveal/index.php
 * decrypt it with application secret and
 * re-encrypt it with used passphrase
 *
 * @param $ID
 * @param $APP_SECRET
 * @param $CIPHER_SECRET
 * @param $CIPHER_RING
 * @param $MYSQLI
 * @return array|bool
 */
function unlockPaste($ID, $APP_SECRET, $CIPHER_SECRET, $CIPHER_RING, $MYSQLI) {
    $PROVIDED_ID = $MYSQLI->real_escape_string($ID);
    $OPTIONS = 0;
    $IV = $APP_SECRET;
    $KEY = $CIPHER_SECRET;
    $stmt = $MYSQLI->prepare("SELECT paste_title, paste_content, paste_pass, paste_hash FROM user_pastes WHERE paste_id = ?");
    if (
        $stmt &&
        $stmt -> bind_param('s', $PROVIDED_ID) &&
        $stmt -> execute() &&
        $stmt -> store_result() &&
        $stmt -> bind_result($title, $content, $pass, $hash) &&
        $stmt -> fetch()
    ) {
        $title = openssl_decrypt($title, $CIPHER_RING, $KEY, $OPTIONS, $IV);
        $content = openssl_decrypt($content, $CIPHER_RING, $KEY, $OPTIONS, $IV);

        // encrypt data with sha1-hash of password and return
        return [openssl_encrypt($hash, $CIPHER_RING, $pass, $OPTIONS, $IV), openssl_encrypt($title, $CIPHER_RING, $pass, $OPTIONS, $IV), openssl_encrypt($content, $CIPHER_RING, $pass, $OPTIONS, $IV)];
    } else {
        // something went wrong...!
        return false;
    }
}

/**
 * Store a new Paste
 *
 * @param $APP_SECRET
 * @param $CIPHER_SECRET
 * @param $CIPHER_RING
 * @param $MYSQLI
 * @param $PASTE
 * @return string|\http\Exception
 */
function safePaste($APP_SECRET, $CIPHER_SECRET, $CIPHER_RING, $MYSQLI, $PASTE) {

    if(!isset($PASTE)) die("ERROR: Internal error.");

    $PASTE_ID = $PASTE[0];
    $PASTE_CONTENT = $PASTE[1];
    $PASTE_TITLE = $PASTE[2];
    $PASTE_PASS = $PASTE[3];
    $ID = $PASTE[4];
    $PASTE_HASH = hash_hmac('sha256', $PASTE_TITLE."|".$PASTE_CONTENT."|".$ID."|".$PASTE_ID, $APP_SECRET);

    $IV_LENGTH = openssl_cipher_iv_length($CIPHER_RING);
    $OPTIONS = 0;
    $IV = $APP_SECRET;
    $KEY = $CIPHER_SECRET;

    $PASTE_TITLE = openssl_encrypt($PASTE_TITLE, $CIPHER_RING, $KEY, $OPTIONS, $IV);
    $PASTE_CONTENT = openssl_encrypt($PASTE_CONTENT, $CIPHER_RING, $KEY, $OPTIONS, $IV);

    $stmt = $MYSQLI->prepare("INSERT INTO user_pastes (paste_id, paste_author, paste_pass, paste_title, paste_content, paste_hash) VALUES (?, ?, ?, ?, ?, ?)");
    $stmt->bind_param("ssssss", $PASTE_ID, $ID, $PASTE_PASS, $PASTE_TITLE, $PASTE_CONTENT, $PASTE_HASH);

    if($stmt->execute()) {
        echo "success";
    } else {
        header('HTTP/1.0 500 Internal Server Error');
    }
}

/**
 * Delete a Paste
 *
 * @param $APP_SECRET
 * @param $CIPHER_SECRET
 * @param $CIPHER_RING
 * @param $MYSQLI
 * @param null $PASTE
 */
function deletePaste($APP_SECRET, $CIPHER_SECRET, $CIPHER_RING, $MYSQLI, $PASTE=null) {
    $ID = $_SESSION['id'];
    if($PASTE !== null) $PASTE_ID = $MYSQLI->real_escape_string($PASTE);
    else $PASTE_ID = htmlspecialchars($MYSQLI->real_escape_string($_POST['delete_id']));

    $stmt = $MYSQLI->prepare("DELETE FROM user_pastes WHERE paste_author = ? AND paste_id = ?");
    $stmt->bind_param("ss", $ID, $PASTE_ID);

    if($stmt->execute()) {
        echo "success";
    } else {
        header('HTTP/1.0 500 Internal Server Error');
    }
}

/**
 * Update an existing Paste
 *
 * @param $APP_SECRET
 * @param $CIPHER_SECRET
 * @param $CIPHER_RING
 * @param $MYSQLI
 */
function updatePaste($APP_SECRET, $CIPHER_SECRET, $CIPHER_RING, $MYSQLI) {
    $ID = $_SESSION['id'];
    $PASTE_ID = htmlspecialchars($MYSQLI->real_escape_string($_POST['update_id']));
    $PASTE_CONTENT = htmlspecialchars($MYSQLI->real_escape_string($_POST['update_content']));
    $PASTE_TITLE = htmlspecialchars($MYSQLI->real_escape_string($_POST['update_title']));
    $PASTE_HASH = hash_hmac('sha256', $PASTE_TITLE."|".$PASTE_CONTENT."|".$ID."|".$PASTE_ID, $APP_SECRET);

    $OPTIONS = 0;
    $IV = $APP_SECRET;
    $KEY = $CIPHER_SECRET;

    $PASTE_TITLE = openssl_encrypt($PASTE_TITLE, $CIPHER_RING, $KEY, $OPTIONS, $IV);
    $PASTE_CONTENT = openssl_encrypt($PASTE_CONTENT, $CIPHER_RING, $KEY, $OPTIONS, $IV);

    $stmt = $MYSQLI->prepare("UPDATE user_pastes SET paste_content = ?, paste_title = ?, paste_hash = ? WHERE paste_author = ? AND paste_id = ?");
    $stmt->bind_param("sssss", $PASTE_CONTENT, $PASTE_TITLE, $PASTE_HASH, $ID, $PASTE_ID);

    if($stmt->execute()) {
        echo "success";
    } else {
        header('HTTP/1.0 500 Internal Server Error');
    }
}

/**
 * Calculate HMAC with application secret
 * as passphrase
 *
 * @param $string
 * @param $APP_SECRET
 * @return string
 */
function calc_checksum($string, $APP_SECRET) {
    return hash_hmac('sha256', $string, $APP_SECRET);
}