const db = require('../models');
const simulations = require('../models/simulations');

module.exports.getAllUserSimulations = getAllUserSimulations;
module.exports.getLatestUserSimulation = getLatestUserSimulation;

/**
 * Get all user settings
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function getAllUserSimulations(ctx, next) {
    
    const userId = +ctx.params.userId;
    if (!userId) ctx.throw(400, 'Missing user ID');

    const activeConnection = await db.connect();
    const res = await simulations.getAllUserSimulations(ctx.params.userId);
    await activeConnection.release();

    ctx.body = {
        data: res
    }
}

/**
 * Get lastest user settings
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function getLatestUserSimulation(ctx, next) {
    const userId = +ctx.params.userId;
    if (!userId) ctx.throw(400, 'Missing user ID');

    const activeConnection = await db.connect();
    const res = await simulations.getLatestUserSimulation(ctx.params.userId);
    await activeConnection.release();

    ctx.body = {
        data: res
    }
}