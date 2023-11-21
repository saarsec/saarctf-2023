<?php

// Network-Time-Protocol API

// variables and configs
require("../func/config.php");

// ensure that requester knows super-duper-secret
$additional_time_formatter = (isset($_GET['modifiers'])) ? $_GET['modifiers'] : "";
$caller_nonce = (isset($_GET['nonce'])) ? $_GET['nonce'] : "";
$caller_checksum = (isset($_GET['checksum'])) ? $_GET['checksum'] : "";

if(isset($_GET['modifiers'])) {
    $nonce_hash = hash_hmac('sha256', $caller_nonce, $APP_SECRET);
    $checksum = hash_hmac('sha256', $additional_time_formatter, $nonce_hash);

    // if the checksum is wrong, the requester is a bad guy who
    // doesn't know the secret
    if($checksum !== $caller_checksum) {
        die("ERROR: Checksum comparison has failed!");
    }
}
// print current time
$time_command = ($APP_HOST === 'win') ? "date /t && time /t" : "date";
$requested_time = `$time_command $additional_time_formatter`;
echo preg_replace('~[\r\n]+~', '', $requested_time);