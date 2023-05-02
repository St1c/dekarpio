const Router = require('koa-router');
const simulationResultsController = require('../controllers/simulation-results.controller');

const router = new Router();

router
    .get('/:userId', simulationResultsController.getLatestUserSimulation)
    .get('/last/:userId/:limit', simulationResultsController.getLastXUserSimulations)
    .get('/all/:userId', simulationResultsController.getAllUserSimulations)
    .put('/:simulationId', simulationResultsController.updateSimulationWithResult);
module.exports = router;