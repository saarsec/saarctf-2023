<?php

// Check for a valid session
if(!isset($_SESSION['authenticated']) || $_SESSION['authenticated'] !== "yes") {
    header('Location: /admin');
    exit();
}