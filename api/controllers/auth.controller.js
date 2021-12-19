const db = require('../models');
const users = require('../models/users');

const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

module.exports.authenticateUser = authenticateUser;

async function authenticateUser(ctx, next) {
    const activeConnection = await db.connect();
    const user = await users.find({
        email: ctx.request.body.email
    });
    if (user.length === 0) {
        await activeConnection.release();
        ctx.throw(401, 'User not found');
    }

    let match = await bcrypt.compare(ctx.request.body.password, user[0].password);
    await activeConnection.release();
    if (!match) ctx.throw(401, 'Auth failed');

    ctx.body = {
        token: jwt.sign({
            id: user[0].id,
            admin: user[0].admin,
            email: ctx.request.body.email
        },
            process.env.APP_SECRET, {
            expiresIn: "30d"
        }
        )
    };
}