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

    const user = await users.find({
        id: ctx.params.id
    });

    if (user.length == 0) {
        await activeConnection.release();
        ctx.throw(404, 'User not found!');
    }

    await simulations.update({
        id: ctx.params.id,
        ...ctx.request.body
    });

    await activeConnection.release();

    ctx.status = 201;
    ctx.body = {
        data: 'User updated'
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

    const activeConnection = await db.connect();

    const user = await users.find({
        id: ctx.params.id
    });

    if (user.length == 0) {
        await activeConnection.release();
        ctx.throw(404, 'User not found!');
    }

    await simulations.delete(ctx.params.id);

    await activeConnection.release();

    ctx.status = 201;
    ctx.body = {
        data: 'User deleted'
    };
}
