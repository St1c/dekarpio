const Router = require('koa-router');

const koajwt = require('koa-jwt');
const authorize = require('../middlewares/auth.middleware');

const authRouter = require('./auth.router');
const filesRouter = require('./files.router');
const protectedRouter = require('./protected.router');
const studiesRouter = require('./studies.router');
const usersRouter = require('./users.router');

const router = new Router();

router
    .use('/api/auth', authRouter.routes())
    .use('/api/files', filesRouter.routes())
    .use(authorize)
    .use(koajwt({secret: process.env.APP_SECRET}))
    .use('/api/studies', studiesRouter.routes())
    .use('/api/private', protectedRouter.routes())
    .use('/api/users', usersRouter.routes());

module.exports = router;