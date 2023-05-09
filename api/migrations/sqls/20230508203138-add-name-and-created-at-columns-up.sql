/* Replace with your SQL commands */
/* add name as string column after id and updated_at column as timestamp after created_at to simulations table */
ALTER TABLE `simulations`
ADD COLUMN `name` VARCHAR(255) NOT NULL AFTER `user_id`,
ADD COLUMN `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER `created_at`;