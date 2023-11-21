<?php

    session_start();
    session_regenerate_id();

    // keeps bad people away
    require("../../func/auth.php");

    // paste functions
    require("../../func/lib/paste.php");

    // variables and configs
    require("../../func/config.php");

    $pastes = loadPastes($APP_SECRET, $CIPHER_SECRET, $CIPHER_RING, $MYSQLI);
    $pasteCount = count($pastes);

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
    <script src="/js/purge.js"></script>
</head>

<body class="dashboard">
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
              <a class="dropdown-item" href="/admin/paste">Create Paste</a>
              <a class="dropdown-item" data-toggle="modal" data-target="#confirmation_enter" onclick="callNTP();">Purge Pastes</a>
              <a class="dropdown-item" onclick="(function() { document.cookie = 'visited=0;' })()">Reset Cookies</a>
              <div class="dropdown-divider"></div>
              <h6 class="dropdown-header">Account</h6>
              <a class="dropdown-item" href="/func/logout.php">Logout</a>
            </div>
          </div>
        </div>
      </div>
      <?php include('../../includes/breadcrumbs.php'); ?>
    </header>

    <?php if(!isset($_COOKIE['visited']) || $_COOKIE['visited'] !== "1"): ?>
    <button id="close" onclick="(function() { $('#jumbotron, #close').remove(); document.cookie = 'visited=1;'; })()" type="button" class="close" aria-label="Close">
        <span aria-hidden="true">&times;</span>
    </button>
    <section id="jumbotron" class="jumbotron text-center">
        <div class="container">
            <h1 class="jumbotron-heading">Welcome, <strong><?php echo $_SESSION['name']; ?></strong></h1>
            <p class="lead text-muted">This is your secure and private working space. Feel free to edit, delete, view or create new pastes. In the navigation bar, you have the option to chose any of the available actions.</p>
            <p>
                <a href="/admin/paste" class="btn btn-primary my-2">New Paste</a>
            </p>
        </div>
    </section>
    <?php endif; ?>

    <main>
      <div class="album py-5">
        <div class="container">
            <div id="paste-list" class="row">
            <!-- Load all pastes -->
            <?php
                if($pasteCount<= 0) {
                  echo "<h3 class='no-pastes'>No Pastes found!</h3>";
                } else {
                  foreach($pastes as $paste) {
                    $id = $paste["paste_id"];
                    $title = (strlen($paste["paste_title"]) >= 18) ? substr($paste["paste_title"], 0, 18) . "..." : $paste["paste_title"];
                    $checksum = $paste["paste_hash"];
                    $content = (strlen($paste["paste_content"]) >= 125) ? substr($paste["paste_content"], 0, 125) . "..." : $paste["paste_content"];

                    echo "<div id=\"paste-card-" . $id . "\" class=\"col-md-4\">
                            <div class=\"card mb-4 box-shadow\">
                                <div class=\"card-body\">
                                    <h3 class=\"card-title\">" . $title . "</h3>
                                    <p class=\"card-text\">" . $content . "</p>
                                    <div class=\"d-flex justify-content-between align-items-center\">
                                        <div class=\"btn-group\">
                                            <button onclick=\"window.open('/reveal/?id=" . $id . "&checksum=" . $checksum . "')\" type=\"button\" class=\"btn btn-sm btn-outline-secondary\">View</button>
                                            <button onclick=\"window.location.href='/admin/paste/?edit=" . $id . "'\" type=\"button\" class=\"btn btn-sm btn-outline-secondary\">Edit</button>
                                            <button onclick=\"deletePaste('" . $id . "');\" type=\"button\" class=\"btn btn-sm btn-outline-danger\">Delete</button>
                                        </div>
                                        <small class=\"text-muted\">id: " . $id . "</small>
                                    </div>
                                    <div class=\"form-group\">
                                        <div id=\"error-" . $id . "\" class=\"alert alert-danger mt-3 hidden\" role=\"alert\">
                                            <span id=\"error_message-" . $id . "\"></span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>\n";
                  }
                }
            ?>
            <!-- End pastes -->
            </div>

        </div>
      </div>
    </main>

    <footer>
      <!-- Purge Confirmation Modal -->
      <div class="modal fade" id="confirmation_enter" tabindex="-1" role="dialog" aria-labelledby="modaltitle" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered" role="document">
              <div class="modal-content">
                <div class="modal-header">
                  <h5 id="modaltitle" class="modal-title">Confirmation required:</h5>
                  <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                  </button>
                </div>
                <div class="modal-body">
                  <div class="form-group">
                    <label for="password">Please enter the following timestamp to confirm:<br/><code id="timestamp"></code></label>
                    <input type="text" class="form-control" placeholder="Timestamp" id="entered_timestamp">
                  </div>
                  <div id="error-confirmation" class="alert alert-danger mt-3 hidden" role="alert">
                    <span id="error_message-confirmation"></span>
                  </div>
                  <div id="success-confirmation" class="alert alert-success hidden" role="alert">
                    <span id="success_message-confirmation"></span>
                  </div>
                </div>
                <div class="modal-footer">
                  <button type="button" id="confirm_purge" onclick="purgeAllPastes()" class="btn btn-primary">Purge!</button>
                  <button type="button" id="cancel_purge" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                  <button type="button" id="finish_purge" onclick="setTimeout(function() { $('#entered_timestamp').val('');$('#confirm_purge, #finish_purge, #cancel_purge').toggleClass('hidden');}, 1000);" data-dismiss="modal" class="btn btn-primary hidden">Finish and close</button>
                </div>
              </div>
            </div>
        </div>
    </footer>
</body>

</html>