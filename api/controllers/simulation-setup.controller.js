const db = require('../models');
const users = require('../models/users');
const simulations = require('../models/simulations');

module.exports.createSimulation = createSimulation;
module.exports.updateSimulation = updateSimulation;
module.exports.deleteSimulation = deleteSimulation;

/**
 * Create new user
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function createSimulation(ctx, next) {
    const user = ctx.state.user;
    if (!user) ctx.throw(403, 'Unknown user');

    console.log(user);
    console.log(ctx.request.body);

    const activeConnection = await db.connect();

    await simulations.create({
        user_id: user.id,
        name: ctx.request.body.name || 'No name set',
        settings: ctx.request.body.settings
    });
    await activeConnection.release();

    ctx.status = 201;
    ctx.body = {
        data: 'Settings saved'
    };
}

/**
 * Update existing user by ID
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function updateSimulation(ctx, next) {
    if (!ctx.state.user) ctx.throw(403, 'Unknown user');

    const activeConnection = await db.connect();

    const simulation = await simulations.find({
        id: ctx.params.id
    });

    if (simulation.length == 0) {
        await activeConnection.release();
        ctx.throw(404, 'Simulation not found!');
    }

    await simulations.update({
        id: ctx.params.id,
        ...ctx.request.body
    });

    await activeConnection.release();

    ctx.status = 201;
    ctx.body = {
        data: 'Simulation updated'
    };
}

/**
 * Delete single user by ID
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function deleteSimulation(ctx, next) {
    if (!ctx.state.user) ctx.throw(403, 'Unknown user');

    const simulationID = ctx.params.id;

    const activeConnection = await db.connect();

    const simulation = await simulations.find({
        id: simulationID
    });

    if (simulation.length == 0) {
        await activeConnection.release();
        ctx.throw(404, 'Simulation id not found!');
    }

    await simulations.delete(simulationID);

    await activeConnection.release();

    ctx.status = 201;
    ctx.body = {
        data: {
            id: simulationID,
            msg: 'Simulation deleted'
        }
    };
}
