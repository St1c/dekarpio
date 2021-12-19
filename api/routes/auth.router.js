const Router = require('koa-router');
const authController = require('../controllers/auth.controller');

const router = new Router();

router
    .post('/login', authController.authenticateUser);

module.exports = router;