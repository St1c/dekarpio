const Router = require('koa-router');
const usersController = require('../controllers/users.controller');

const router = new Router();

router
    .get('/', usersController.getAllUsers)
    .get('/:id', usersController.getUser)
    .post('/', usersController.createUser)
    .put('/:id', usersController.updateUser)
    .delete('/:id', usersController.deleteUser);

module.exports = router;