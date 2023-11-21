SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


CREATE TABLE `user_accounts` (
  `user_id` SERIAL,
  `user_name` varchar(255) DEFAULT NULL,
  `user_pass` varchar(255) DEFAULT NULL,
  `created_at` int(6) DEFAULT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE `user_pastes` (
  `paste_id` varchar(255) NOT NULL,
  `paste_author` BIGINT UNSIGNED NOT NULL,
  `paste_pass` varchar(255) DEFAULT NULL,
  `paste_title` varchar(255) DEFAULT NULL,
  `paste_content` varchar(600) DEFAULT NULL,
  `paste_hash` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`paste_id`),
  FOREIGN KEY (`paste_author`) REFERENCES `user_accounts` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

COMMIT;