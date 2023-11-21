<?php

/**
 * Generates a new challenge
 *
 * @return string
 */
function generateChallenge() {
    mt_srand(time());

    $strength = 6;
    $alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    $l = strlen($alpha);
    $random_string = '';
    for($i = 0; $i < $strength; $i++) {
        $random_character = $alpha[mt_rand(0, $l - 1)];
        $random_string .= $random_character;
    }

    $_SESSION['challenge'] = $random_string;
    return $random_string;
}

/**
 * Destroys challenge
 */
function destroyChallenge() {
    unset($_SESSION['challenge']);
}