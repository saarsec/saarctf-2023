<?php

session_start();
session_regenerate_id();

// forward the good bois
if(isset($_SESSION["authenticated"]) && $_SESSION["authenticated"] === "yes") {
    header('Location: /admin/home');
    exit();
}

?>

<!DOCTYPE html>
<html lang="en">

<head>
    <title>Pasteable</title>
    <meta charset="utf-8">

    <?php include('../includes/viewport.php'); ?>

    <!-- Style Sheets -->
    <link rel="stylesheet" href="/css/lib/bootstrap.min.css">
    <link rel="stylesheet" href="/css/main.css">

    <!-- Scripts -->
    <script src="/js/lib/jquery.min.js"></script>
    <script src="/js/lib/bootstrap.bundle.min.js"></script>
    <script src="/js/lib/crypto-js.js"></script>
    <script src="/js/forms.js"></script>
    <script src="/js/login.js"></script>
</head>

<body class="pattern">
<div class="form-center">
    <div class="form-content">
        <div class="card">
            <article class="card-body">
                <form id="loginform">
                    <div id="credentials">
                        <h4 class="card-title mb-4 mt-1">Login</h4>
                        <div class="form-group">
                            <label>Your username</label>
                            <input id="username" name="username" class="form-control" placeholder="Username" type="text">
                        </div>
                        <div class="form-group">
                            <label>Your password</label>
                            <input required id="password" name="password" class="form-control" placeholder="******" type="password">
                            <div class="invalid-feedback">Password can't be empty.</div>
                        </div>
                        <div class="form-group">
                            <div id="error" class="alert alert-danger hidden" role="alert">
                                <span id="error_message"></span>
                            </div>
                        </div>
                    </div>
                    <div class="form-group">
                        <button id="submitbtn" class="btn btn-primary btn-block">Login / Register</button>
                    </div>
                </form>
            </article>
        </div>
    </div>
</div>
</body>

<footer>
    <!-- Form Submission -->
    <script type="text/javascript">
        $('#submitbtn').click(function(e) {
            e.preventDefault();
            e.stopPropagation();

            submitLogin();
        });
    </script>
</footer>

</html>