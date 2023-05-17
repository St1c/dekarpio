const db = require('../models');
const simulations = require('../models/simulations');

module.exports.getAllUserSimulations = getAllUserSimulations;
module.exports.getLastUserSimulations = getLastUserSimulations;
module.exports.getLatestUserSimulation = getLatestUserSimulation;
module.exports.getUserSimulationById = getUserSimulationById;
module.exports.updateSimulationWithResult = updateSimulationWithResult;

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
    const res = await simulations.getAllUserSimulations(userId);
    await activeConnection.release();

    ctx.body = {
        data: res
    }
}

async function getLastUserSimulations(ctx, next) {
    const userId = +ctx.params.userId;
    const limit = +ctx.params.limit;
    if (!userId) ctx.throw(400, 'Missing user ID');

    const activeConnection = await db.connect();
    const res = await simulations.getLastUserSimulations(userId, limit);
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


/**
 * Get lastest user settings
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function getUserSimulationById(ctx, next) {
    const userId = +ctx.params.userId;
    if (!userId) ctx.throw(400, 'Missing user ID');

    const simulationId = +ctx.params.simulationId;
    if (!simulationId) ctx.throw(400, 'Missing simulation ID');

    const activeConnection = await db.connect();
    const res = await simulations.getUserSimulationById(userId, simulationId);
    await activeConnection.release();

    ctx.body = {
        data: res
    }
}

/**
 * Update existing simulation by ID with result
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function updateSimulationWithResult(ctx, next) {

    const simulationId = +ctx.params.simulationId;
    console.log(simulationId)
    if (!simulationId) ctx.throw(400, 'Missing simulation ID');

    const activeConnection = await db.connect();

    await simulations.update({
        id: simulationId,
        results: ctx.request.body.results
    });

    await activeConnection.release();

    ctx.status = 201;
    ctx.body = {
        data: 'Simulation updated with result'
    };
}