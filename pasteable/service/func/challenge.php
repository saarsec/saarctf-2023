<?php

// include configs for globals
include('config.php');

// include challenge functions
include('./lib/challenge.php');

session_start();
session_regenerate_id();

if(isset($_POST['username'])) {
    $username = $_POST['username'];
    $stmt = $MYSQLI->prepare("SELECT user_pass FROM user_accounts WHERE user_name = ? LIMIT 1");

    if (
        $stmt &&
        $stmt -> bind_param('s', $username) &&
        $stmt -> execute() &&
        $stmt -> store_result() &&
        $stmt -> bind_result($userpassword) &&
        $stmt -> fetch()
    ) {
        // user exists -> generate challenge
        $challenge = generateChallenge();
        $key = hex2bin($userpassword);
        $iv = substr($key, 0, 16);
        $challenge_enc = openssl_encrypt($challenge, "AES-256-CBC", $key, OPENSSL_RAW_DATA, $iv);
        echo bin2hex($challenge_enc);
    } else{
        echo "ok";
    }
    
} else {
    header('HTTP/1.0 403 Forbidden');
    exit();
}
