const Router = require('koa-router');
const simulationResultsController = require('../controllers/simulation-results.controller');

const router = new Router();

router
    .get('/:userId', simulationResultsController.getLatestUserSimulation)
    .get('/all/:userId', simulationResultsController.getAllUserSimulations);
module.exports = router;