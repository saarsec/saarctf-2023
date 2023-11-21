<?php

// destroy session
session_start();
session_unset();
session_destroy();

// redirect to main page
header("Location: ../");

// stop execution
die();