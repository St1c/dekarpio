const Router = require('koa-router');

const koajwt = require('koa-jwt');
const authorize = require('../middlewares/auth.middleware');

const authRouter = require('./auth.router');
const protectedRouter = require('./protected.router');
const simulationResultsRouter = require('./simulation-results.router');
const simulationSetupRouter = require('./simulation-setup.router');
const usersRouter = require('./users.router');

const router = new Router();

router
    .use('/api/auth', authRouter.routes())
    .use('/api/simulation-results', simulationResultsRouter.routes())
    .use(authorize)
    .use(koajwt({ secret: process.env.APP_SECRET }))
    .use('/api/private', protectedRouter.routes())
    .use('/api/simulation-setup', simulationSetupRouter.routes())
    .use('/api/users', usersRouter.routes());

module.exports = router;