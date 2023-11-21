<?php

    session_start();
    session_regenerate_id();

    // keeps bad people away
    require("../../func/auth.php");

    // paste functions
    require("../../func/lib/paste.php");

    // variables and configs
    require("../../func/config.php");

    $EDIT_MODE = false;

    if(isset($_GET['edit'])) {
        $ID = $_GET['edit'];
        $EDIT_MODE = true;
        $retrieved_data = loadPasteToEdit($ID, $APP_SECRET, $CIPHER_SECRET, $CIPHER_RING, $MYSQLI);
    }

    $paste_id = ($EDIT_MODE === true) ? $ID : uniqid();
    $share_url = "/reveal/?id=".$paste_id."&checksum=";

?>
<!DOCTYPE html>
<html lang="en">

<head>
    <title>Pasteable</title>
    <meta charset="utf-8">

    <?php include('../../includes/viewport.php'); ?>

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
    <script src="/js/paste.js"></script>
</head>

<body>
    <header>
      <div id="navbar" class="navbar navbar-dark bg-dark box-shadow">
        <div class="container d-flex justify-content-between">
          <a href="#" class="navbar-brand d-flex align-items-center">
            <strong class="page-path">pasteable</strong>
          </a>
          <div class="dropdown">
            <button class="nav-link text-light border-0 bg-transparent dropdown-toggle" type="button" id="menulink" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                <i class="fas fa-user-cog"></i>&nbsp;&nbsp;<?php echo $_SESSION['name']; ?>
            </button>
            <div class="dropdown-menu" aria-labelledby="menulink">
              <h6 class="dropdown-header">Choose Action</h6>
              <a class="dropdown-item" href="/admin/home">Go Back</a>
              <div class="dropdown-divider"></div>
              <h6 class="dropdown-header">Account</h6>
              <a class="dropdown-item" href="/func/logout.php">Logout</a>
            </div>
          </div>
        </div>
      </div>
      <?php include('../../includes/breadcrumbs.php'); ?>
    </header>

    <main>
        <diV class="py-5">
            <div class="container modified">
                <h2><?php echo (($EDIT_MODE === true) ? "Edit" : "New"); ?> secure Paste</h2>
                <form id="pasteform">
                    <div class="form-group">
                        <label for="title">Title:</label>
                        <input required name="title" type="text" class="form-control" placeholder="Lorem Ipsum" id="title" <?php echo (($EDIT_MODE === true) ? "value=\"".$retrieved_data[0]."\"" : "");?>>
                        <div class="invalid-feedback">Title can't be empty.</div>
                    </div>
                    <div class="form-group">
                        <label for="contentarea">Content:</label>
                        <textarea required name="content" class="form-control" id="contentarea" rows="3" placeholder="Dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat"><?php echo (($EDIT_MODE === true) ? $retrieved_data[1] : "");?></textarea>
                        <div class="invalid-feedback">Content can't be empty.</div>
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input required <?php echo (($EDIT_MODE === true) ? "disabled" : ""); ?> name="password" type="password" class="form-control" placeholder="********" id="password">
                        <div class="invalid-feedback">Password can't be empty.</div>
                    </div>
                    <div class="form-group">
                        <label for="id">ID:</label>
                        <input name="id" type="text" class="form-control" id="id" value="<?php echo $paste_id ?>" readonly>
                        <a id="share_url" href="<?php echo $share_url . (($EDIT_MODE === true) ? $retrieved_data[3] : ""); ?>"><?php echo $share_url  . (($EDIT_MODE === true) ? $retrieved_data[3] : ""); ?></a>
                    </div>
                    <div class="form-group">
                    <div id="error" class="alert alert-danger hidden" role="alert">
                        <span id="error_message"></span>
                    </div>
                    </div>
                    <div class="form-group">
                    <div id="success" class="alert alert-success hidden" role="alert">
                        <span id="success_message"></span>
                    </div>
                    </div>
                    <button id="submitbtn" class="btn btn-primary"><?php echo (($EDIT_MODE === true) ? "Save Changes" : "Create and Publish"); ?></button>
                </form>
            </div>
        </div>
    </main>

    <footer>
        <!-- Background Workflow -->
        <script type="text/javascript">
            // TODO: YOU LEAK HOW THE CHECKSUM IS CONSTRUCTED!! FIX THAT!
            $('input,textarea').on("input", function(e) {
                let title = $('#title').val();
                let content = $('#contentarea').val();
                let id = "<?php echo $paste_id; ?>";
                let author = "<?php echo $_SESSION['id']; ?>";
                $.post('../../func/paste.php', {"calc_checksum": `${title}|${content}|${author}|${id}`})
                .done(function(response) {
                    $('#share_url').html("<?php echo $share_url; ?>" + response);
                    $('#share_url').attr("href", "<?php echo $share_url; ?>" + response);
                })
                .fail(function(xhr, status, error) {
                    showError("Invalid user credentials");
                });
            });

            // create paste as background workflow
            $('#submitbtn').on("click", function(e) {
                e.preventDefault();
                e.stopPropagation();

                submitPaste();
            });
        </script>
    </footer>
</body>

</html>