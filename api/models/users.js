const db = require('./index');
const mysql = require('mysql');
const bcrypt = require('bcrypt');

// Readble attributes contains password (for bcrypt internal JWT checking), 
// all data sent to user must be pruned before sending
const readable = ['id', 'company', 'email', 'password', 'admin'];
const writable = ['id', 'company', 'email', 'password', 'admin'];

var users = Object.assign(Object.create(db), {
    create,
    getAllUsers,
    update,
    getAllNonAdminUsers
});
users.init('users', readable, writable);
module.exports = users;

async function create(userObj) {
    this.checkIfWritableAttributeExists(userObj);

    const saltRounds = 4;
    const pass = await bcrypt.hash(userObj.password, saltRounds);

    userObj = {
        ...userObj,
        password: pass,
        admin: userObj.admin ? 1 : 0
    };

    return this.query(mysql.format(
        'INSERT INTO ?? SET ?', [this.tableName, userObj]
    ));
}

async function update(userObj) {
    if (!userObj.hasOwnProperty('id')) {
        throw new Error('Missing ID, user update failed!');
    }

    if (userObj.password !== '') {
        const saltRounds = 4;
        const pass = await bcrypt.hash(userObj.password, saltRounds);
        userObj.password = pass;
    }

    this.checkIfWritableAttributeExists(userObj);

    return this.query(mysql.format(
        'UPDATE ?? SET ? WHERE `id` = ?', [this.tableName, userObj, userObj.id]
    ));
}


async function getAllUsers() {
    let res = await this.query(mysql.format(
        'SELECT ?? FROM ??;', [this.readableAttributes, this.tableName]
    ));

    return res.map(row => {
        // Remove password from the results
        const { password, ...res } = row;
        return res;
    });
}

async function getAllNonAdminUsers() {
    let res = await this.query(mysql.format(
        'SELECT ?? FROM ?? WHERE admin = 0;', [this.readableAttributes, this.tableName]
    ));

    return res.map(row => {
        // Remove password from the results
        const { password, admin, ...res } = row;
        return res;
    });
}