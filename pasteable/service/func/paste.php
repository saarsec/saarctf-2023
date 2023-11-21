<?php

require("config.php");
require("lib/paste.php");

// create checksums
if(isset($_POST['calc_checksum'])) {
    echo calc_checksum($_POST['calc_checksum'], $APP_SECRET);
}

// decrypt any text-pass-combinations
if(isset($_POST['cipher'])) {
    echo openssl_decrypt($_POST['cipher'], $CIPHER_RING, sha1($_POST['cipher_pass']), 0, $APP_SECRET);
}

// handle new paste
if(isset($_POST['title']) && isset($_POST['content']) && isset($_POST['password']) && isset($_POST['id'])) {
    session_start();
    require("auth.php");

    $PASTE_ID = htmlspecialchars($MYSQLI->real_escape_string($_POST['id']));
    $PASTE_CONTENT = htmlspecialchars($MYSQLI->real_escape_string($_POST['content']));
    $PASTE_TITLE = htmlspecialchars($MYSQLI->real_escape_string($_POST['title']));
    $PASTE_PASS = sha1(htmlspecialchars($MYSQLI->real_escape_string($_POST['password'])));    
    $ID = $_SESSION['id'];
    safePaste($APP_SECRET, $CIPHER_SECRET, $CIPHER_RING, $MYSQLI, [$PASTE_ID, $PASTE_CONTENT, $PASTE_TITLE, $PASTE_PASS, $ID]);
}

// handle delete paste
if(isset($_POST['delete_id'])) {
    session_start();
    require("auth.php");
    deletePaste($APP_SECRET, $CIPHER_SECRET, $CIPHER_RING, $MYSQLI);
}

// handle update paste
if(isset($_POST['update_id'])) {
    session_start();
    require("auth.php");
    updatePaste($APP_SECRET, $CIPHER_SECRET, $CIPHER_RING, $MYSQLI);
}