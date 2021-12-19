const Router = require('koa-router');

const router = new Router();

router.get('/', async ctx => ctx.body = 'Welcome to private dekarpio API');

module.exports = router;