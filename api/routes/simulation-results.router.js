const Router = require('koa-router');
const simulationResultsController = require('../controllers/simulation-results.controller');

const router = new Router();

router
    .get('/:userId', simulationResultsController.getLatestUserSimulation)
    .get('/simulation/:userId/:simulationId', simulationResultsController.getUserSimulationById)
    .get('/last/:userId/:limit', simulationResultsController.getLastUserSimulations)
    .get('/all/:userId', simulationResultsController.getAllUserSimulations)
    .put('/:simulationId', simulationResultsController.updateSimulationWithResult);
module.exports = router;