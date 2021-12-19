const db = require('../models');
const users = require('../models/users');

module.exports.getAllUsers = getAllUsers;
module.exports.getUser = getUser;
module.exports.createUser = createUser;
module.exports.updateUser = updateUser;
module.exports.deleteUser = deleteUser;

/**
 * Get all users
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function getAllUsers(ctx, next) {
    if (!ctx.state.user.admin) ctx.throw(403, 'Not authorized to use this end-point');

    const activeConnection = await db.connect();
    const nonAdminUsers = await users.getAllUsers();
    await activeConnection.release();

    ctx.body = {
        data: nonAdminUsers
    }
}

/**
 * Get single user by ID
 * 
 * @param {Object} ctx Request, response 
 * @param {Object} next Next handler
 */
async function getUser(ctx, next) {
    const activeConnection = await db.connect();

    const user = await users.find({
        id: ctx.params.id
    });
    await activeConnection.release();

    if (user.length == 0) {
        ctx.throw(404, 'User not found!');
    }

    let { password, ...data } = user[0];

    ctx.status = 200;
    ctx.body = { data };
}

/**
 * Create new user
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function createUser(ctx, next) {

    const email = ctx.request.body.email;
    const password = ctx.request.body.password;
    const admin = +ctx.request.body.admin || 0;

    if (!password || !email) ctx.throw(400, 'Missing email or password');

    const activeConnection = await db.connect();

    const user = await users.find({
        email: ctx.request.body.email
    });
    if (user.length !== 0) {
        await activeConnection.release();
        ctx.throw(404, 'User already exists!');
    }

    await users.findOrCreate({
        email,
        password,
        admin,
    });
    await activeConnection.release();

    ctx.status = 201;
    ctx.body = {
        data: 'User created'
    };
}

/**
 * Update existing user by ID
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function updateUser(ctx, next) {
    const activeConnection = await db.connect();

    const user = await users.find({
        id: ctx.params.id
    });

    if (user.length == 0) {
        await activeConnection.release();
        ctx.throw(404, 'User not found!');
    }

    await users.update({
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
async function deleteUser(ctx, next) {
    const activeConnection = await db.connect();

    const user = await users.find({
        id: ctx.params.id
    });

    if (user.length == 0) {
        await activeConnection.release();
        ctx.throw(404, 'User not found!');
    }

    await users.delete(ctx.params.id);

    await activeConnection.release();

    ctx.status = 201;
    ctx.body = {
        data: 'User deleted'
    };
}
