/* Replace with your SQL commands */
CREATE TABLE IF NOT EXISTS `simulations` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `user_id` int(10) unsigned NOT NULL,
    `settings` JSON NOT NULL,
    `results` JSON,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `user_id` FOREIGN KEY (`user_id`) REFERENCES users(`id`)
);