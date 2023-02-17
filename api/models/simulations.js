const db = require('./index');
const mysql = require('mysql');

// Readble attributes contains password (for bcrypt internal JWT checking), 
// all data sent to user must be pruned before sending
const readable = ['id', 'user_id', 'settings', 'results'];
const writable = ['user_id', 'settings', 'results'];

var simulations = Object.assign(Object.create(db), {
    create,
    update,
    getAllUserSimulations,
    getLatestUserSimulation
});
simulations.init('simulations', readable, writable);
module.exports = simulations;

async function create(obj) {
    this.checkIfWritableAttributeExists(obj);

    return this.query(mysql.format(
        'INSERT INTO ?? SET ?', [this.tableName, obj]
    ));
}

async function update(obj) {
    if (!obj.hasOwnProperty('id')) {
        throw new Error('Missing ID, simulations update failed!');
    }

    this.checkIfWritableAttributeExists(obj);

    return this.query(mysql.format(
        'UPDATE ?? SET ? WHERE `id` = ?', [this.tableName, obj, obj.id]
    ));
}

async function getAllUserSimulations(userId) {
    return this.query(mysql.format(
        'SELECT ?? FROM ?? WHERE `user_id` = ?', [this.readableAttributes, this.tableName, userId]
    ));
}

async function getLatestUserSimulation(userId) {
    return this.query(mysql.format(
        'SELECT ?? FROM ?? WHERE `user_id` = ? ORDER BY `created_at` LIMIT 1', [this.readableAttributes, this.tableName, userId]
    ));
}