<?php

session_start();
require("config.php");


if(!isset($_POST['username']) || !isset($_POST['password']))
    die("Invalid request");

$username = $_POST['username'];
$password = $_POST['password'];

// create user
$stmt = $MYSQLI->prepare("INSERT INTO user_accounts(user_name, user_pass) VALUES (?, ?)");
if (
    $stmt -> bind_param('ss', $username, $password) &&
    $stmt -> execute()
) {
    $_SESSION['id'] = $stmt->insert_id;
    $_SESSION['name'] = $username;
    // set new state
    $_SESSION['authenticated'] = "yes";
} else {
    $_SESSION['last_login'] = date("Y-m-d H:i:s", time());
    header('HTTP/1.0 403 Forbidden');
}