<?php

/**
 * User Library
 *
 * Contains all commonly used functions
 * concerning the users
 */

/**
 * Fetch available users from db
 *
 * @param $MYSQLI
 * @return array
 */
function getUserList($MYSQLI) {
    $stmt = $MYSQLI->prepare("SELECT user_id, user_name, created_at FROM user_accounts");
    if (
        $stmt->execute()
    ) {
        $users = array();
        $result = $stmt->get_result();
        while ($row = $result->fetch_assoc()) {
            array_push($users, ["user_id" => $row['user_id'], "user_name" => $row['user_name'], "account_created_at" => $row['created_at']]);
        }
        return $users;
    } else {
        // something went wrong...
        die("ERROR: Could not load users!");
    }
}