<?php
$path = [];

if(!isset($EDIT_MODE)) $EDIT_MODE = NULL;

if($EDIT_MODE !== NULL) {
    if($EDIT_MODE === false) {
        $path = ["paste", "create"];
    } else {
        $path = ["paste", "edit"];
    }
} else {
    $path = ["home"];
}
?>

<!DOCTYPE html>
<html>
<body>
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><?php echo $_SESSION['name']; ?></li>
        <?php
        for($i = 0; $i < count($path); $i++) {
            echo "<li class=\"breadcrumb-item " . (($i === count($path)-1) ? "active" : "") . "\" aria-current=\"page\">" . $path[$i] . "</li>";
        }
        ?>
    </ol>
</nav>
</body>
</html>
