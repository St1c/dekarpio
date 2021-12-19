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
  db.connection.query(`
    INSERT INTO \`users\` (\`company\`, \`email\`, \`password\`, \`admin\`) VALUES 
    ('AIT', 'user1@example.com', '$2b$04$qq8EJPPKcQWH5ayyxL6ZA.rX0XtIrxcvqRaxfXekkzK98Nvp6yCpu', 0)
  `, callback);
};

exports.down = function (db, callback) {
  db.connection.query(`
      DELETE FROM \`users\` WHERE \`email\`='user1@example.com';
  `, callback);
};

exports._meta = {
  'version': 1
};