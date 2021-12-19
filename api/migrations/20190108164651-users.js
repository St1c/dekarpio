'use strict';

var dbm;
var type;
var seed;

/**
  * We receive the dbmigrate dependency from dbmigrate initially.
  * This enables us to not have to rely on NODE_PATH.
  */
exports.setup = function (options, seedLink) {
  dbm = options.dbmigrate;
  type = dbm.dataType;
  seed = seedLink;
};

exports.up = function (db, callback) {
  return db.createTable('users', {
    id: {
      type: 'int',
      notNull: true,
      unsigned: true,
      primaryKey: true,
      autoIncrement: true,
      length: 10
    },
    company: {
      type: 'char',
      notNull: true,
      length: 255
    },
    email: {
      type: 'char',
      notNull: true,
      length: 100
    },
    password: {
      type: 'char',
      notNull: true,
      length: 60
    },
    admin: {
      type: 'boolean',
      notNull: true,
      defaultValue: false
    }
  }, createTimestamps);

  function createTimestamps(err) {
    if (err) {
      callback(err);
      return;
    }

    db.connection.query(`
    ALTER TABLE users
    ADD created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
      ON UPDATE CURRENT_TIMESTAMP
    `, createDefaultAdminUser);
  }

  function createDefaultAdminUser(err) {
    console.log('creating default user...');
    if (err) {
      console.log(err);
      callback(err);
      return;
    }

    db.connection.query("INSERT INTO `users` (`id`, `company`, `email`, `password`, `admin`, `created_at`) VALUES(1, 'AIT','admin@example.com', '$2b$04$6Ynb1Uq3AYLj9twSYJWX6eTaNrIafp6WW7N7L9BRmu8uqUm84u7W6', 1, '2019-01-15 14:37:36')", callback);
  }

};

exports.down = function (db) {
  return db.dropTable('users');
};

exports._meta = {
  "version": 1
};
