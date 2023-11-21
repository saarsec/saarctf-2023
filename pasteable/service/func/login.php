<?php

session_start();
require("config.php");

// include challenge functions
include('./lib/challenge.php');

if(!isset($_POST['username']) || !isset($_POST['solution'])){
    header('HTTP/1.0 403 Forbidden');
    die("Invalid request");
}

if(!isset($_SESSION['challenge']) || !(strcmp($_POST['solution'], $_SESSION['challenge']) == 0)){
    header('HTTP/1.0 403 Forbidden');
    die("No valid challenge found");
}


destroyChallenge();
$username = $_POST['username'];
$stmt = $MYSQLI->prepare("SELECT user_id FROM user_accounts WHERE user_name = ? LIMIT 1");

if (
	$stmt &&
	$stmt -> bind_param('s', $username) &&
	$stmt -> execute() &&
	$stmt -> store_result() &&
	$stmt -> bind_result($userid) &&
	$stmt -> fetch()
) {
    // user exists
    $_SESSION['last_login'] = date("Y-m-d H:i:s", time());
    $_SESSION['id'] = $userid;
    $_SESSION['name'] = $username;
    // set new state
    $_SESSION['authenticated'] = "yes";
} else {
    // wrong data!
    $_SESSION['last_login'] = date("Y-m-d H:i:s", time());
    header('HTTP/1.0 403 Forbidden');
}
