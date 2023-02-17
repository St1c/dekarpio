const Router = require('koa-router');
const simulationSetupController = require('../controllers/simulation-setup.controller');

const router = new Router();

router
    .post('/', simulationSetupController.createSimulation)
    .put('/:id', simulationSetupController.updateSimulation)
    .delete('/:id', simulationSetupController.deleteSimulation);

module.exports = router;