const Router = require('koa-router');
const studiesController = require('../controllers/studies.controller');

const router = new Router();

router
    .get('/', studiesController.getAllStudies)
    .get('/:id', studiesController.getStudy)
    .post('/', studiesController.createStudy)
    .put('/:id', studiesController.updateStudy)
    .delete('/:id', studiesController.deleteStudy);

module.exports = router;