const Router = require('koa-router');
const authController = require('../controllers/auth.controller');

const router = new Router();

router
    .post('/login', authController.authenticateUser)
    .get('/checkJwt', authController.checkJwt);

module.exports = router;