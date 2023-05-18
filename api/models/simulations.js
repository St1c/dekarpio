const db = require('./index');
const mysql = require('mysql');

// Readble attributes contains password (for bcrypt internal JWT checking),
// all data sent to user must be pruned before sending
const readable = ['id', 'user_id', 'name', 'settings', 'results', 'created_at', 'updated_at'];
const writable = ['id', 'user_id', 'name', 'settings', 'results'];

var simulations = Object.assign(Object.create(db), {
    create,
    update,
    getAllUserSimulations,
    getLastUserSimulations,
    getLatestUserSimulation,
    getUserSimulationById,
    getAllUserSimulationsPaginated
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
        'SELECT simulations.id, user_id, name, settings, simulations.created_at, updated_at, ?? FROM ?? JOIN ?? ON ?? = ?? WHERE `user_id` = ? ORDER BY `updated_at` DESC',
        ['users.email', this.tableName, 'users', `${this.tableName}.user_id`, 'users.id', userId]
    ));
}

async function getAllUserSimulationsPaginated(userId, limit, offset) {
    return this.query(mysql.format(
        'SELECT ?? FROM ?? WHERE `user_id` = ? ORDER BY `updated_at` DESC LIMIT ? OFFSET ?',
        [this.readableAttributes, this.tableName, userId, limit, offset]
    ));
}

async function getLastUserSimulations(userId, limit = 10) {
    return this.query(mysql.format(
        'SELECT simulations.id, user_id, name, settings, simulations.created_at, updated_at, ?? FROM ?? JOIN ?? ON ?? = ?? WHERE `user_id` = ? ORDER BY `updated_at` DESC LIMIT ?',
        ['users.email', this.tableName, 'users', `${this.tableName}.user_id`, 'users.id', userId, limit]
    ));
}

async function getLatestUserSimulation(userId) {
    return this.query(mysql.format(
        'SELECT ?? FROM ?? WHERE `user_id` = ? ORDER BY `created_at` DESC LIMIT 1', [this.readableAttributes, this.tableName, userId]
    ));
}


async function getUserSimulationById(userId, simulationId) {
    return this.query(mysql.format(
        'SELECT ?? FROM ?? WHERE `user_id` = ? AND `id` = ? ORDER BY `created_at` DESC LIMIT 1', [this.readableAttributes, this.tableName, userId, simulationId]
    ));
}