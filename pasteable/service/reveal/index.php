<?php

    $ERROR = false;

    // paste functions
    require("../func/lib/paste.php");

    // variables and configs
    require("../func/config.php");

    if(!isset($_GET['id']) || !isset($_GET['checksum'])) {
        $ERROR = true;
        $ERROR_MESSAGE = "Paste information missing";
    } 

    $ID = $_GET['id'];
    $CHECKSUM = $_GET['checksum'];

    $retrieved_data = unlockPaste($ID, $APP_SECRET, $CIPHER_SECRET, $CIPHER_RING, $MYSQLI);
    if($retrieved_data === false) {
        // no paste could be found!
        $ERROR = true;
        $ERROR_MESSAGE = "Paste information invalid";
        $retrieved_data[1] = "Lorem ipsum";
        $retrieved_data[2] = "Dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.";
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
    <link rel="stylesheet" href="/css/lib/zapfino-extra-lt.css" >
    <link rel="stylesheet" href="/css/lib/fontawesome.css">
    <link rel="stylesheet" href="/css/main.css">
    <link rel="stylesheet" href="/css/home.css">

    <!-- Scripts -->
    <script src="/js/lib/jquery.min.js"></script>
    <script src="/js/lib/popper.min.js"></script>
    <script src="/js/lib/bootstrap.bundle.min.js"></script>
    <script src="/js/forms.js"></script>
    <script src="/js/reveal.js"></script>
    <script type="text/javascript">var PASSWORD_WAS_ENTERED = false;</script>
</head>

<body class="pattern">
<div class="form-center">
    <div class="form-content">
        <div class="card">
            <article class="card-body">
                <h2 id="title" class="card-title mb-4 mt-1"><?php echo $retrieved_data[1]; ?></h2>
                <form id="loginform">
                    <div class="form-group">
                        <textarea readonly name="content" class="form-control" id="contentarea" rows="10"><?php echo $retrieved_data[2]; ?></textarea>
                    </div>
                    <div id="error" class="alert alert-danger hidden" role="alert">
                        <span id="error_message"></span>
                    </div>
                    <div class="form-group">
                        <button disabled id="submitbtn" class="btn btn-primary btn-block">Thanks, lock again.</button>
                    </div>
                </form>
            </article>
        </div>
    </div>
</div>
</body>

<footer>
    <div class="modal fade" id="pass_enter" tabindex="-1" role="dialog" aria-labelledby="modaltitle" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 id="modaltitle" class="modal-title">Enter password:</h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" class="form-control" placeholder="********" id="password">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" onclick="PASSWORD_WAS_ENTERED = true; decryptInformation(event, '<?php echo $retrieved_data[0]; ?>', '<?php echo $retrieved_data[1]; ?>', '<?php echo $retrieved_data[2]; ?>', '<?php echo $CHECKSUM; ?>')" class="btn btn-primary">Unlock!</button>
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Lock Again Button -->
    <script type="text/javascript">
        $('#submitbtn').on("click", function(e) {
            e.preventDefault();
            e.stopPropagation();

            PASSWORD_WAS_ENTERED = false;
            $('#title').html("<?php echo $retrieved_data[1]; ?>");
            $('#contentarea').val("<?php echo $retrieved_data[2]; ?>");

            $('#submitbtn').attr("disabled", "true");
            $('#password').val("");
            $('#pass_enter').modal();
        });
    </script>

    <?php
        // invoke new javascript snippets
        if($ERROR) {
            echo "
            <!-- Show error message -->
            <script type=\"text/javascript\">
                showError(\"" . $ERROR_MESSAGE . "\");
            </script>
            ";
        } else {
            echo "
            <!-- Show modal to enter pw -->
            <script type=\"text/javascript\">
                $('#pass_enter').modal()
            </script>
            <!-- Add listeners -->
            <script type=\"text/javascript\">
                $('#pass_enter').on('hidden.bs.modal', function (e) {
                   if(!PASSWORD_WAS_ENTERED) showError('Password is missing.');
                });
            </script>
            ";
        }
    ?>
</footer>