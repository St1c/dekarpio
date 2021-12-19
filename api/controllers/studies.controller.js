const db = require('../models');
const studies = require('../models/studies');

module.exports.getAllStudies = getAllStudies;
module.exports.getStudy = getStudy;
module.exports.createStudy = createStudy;
module.exports.updateStudy = updateStudy;
module.exports.deleteStudy = deleteStudy;

/**
 * Get all studies
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function getAllStudies(ctx, next) {
    // if (!ctx.state.user.admin) ctx.throw(403, 'Not authorized to use this end-point');

    const activeConnection = await db.connect();
    const allStudies = await studies.getAllStudies();
    await activeConnection.release();

    ctx.body = {
        data: allStudies
    }
}

/**
 * Get single study by ID
 * 
 * @param {Object} ctx Request, response 
 * @param {Object} next Next handler
 */
async function getStudy(ctx, next) {
    const activeConnection = await db.connect();

    const study = await studies.find({
        id: ctx.params.id
    });
    await activeConnection.release();

    if (study.length == 0) {
        ctx.throw(404, 'Study not found!');
    }


    ctx.status = 200;
    ctx.body = { ...study[0] };
}

/**
 * Create new study
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function createStudy(ctx, next) {

    const study_name = ctx.request.body.study_name;

    if (!study_name) ctx.throw(400, 'Missing study name');

    const activeConnection = await db.connect();

    const study = await studies.find({
        study_name: ctx.request.body.study_name
    });
    if (study.length !== 0) {
        await activeConnection.release();
        ctx.throw(404, 'Study already exists!');
    }

    await studies.findOrCreate({ ... ctx.request.body });
    await activeConnection.release();

    ctx.status = 201;
    ctx.body = {
        data: 'Study created'
    };
}

/**
 * Update existing user by ID
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function updateStudy(ctx, next) {
    const activeConnection = await db.connect();

    const study = await studies.find({
        id: ctx.params.id
    });

    if (study.length == 0) {
        await activeConnection.release();
        ctx.throw(404, 'Study not found!');
    }

    await studies.update({
        id: ctx.params.id,
        ...ctx.request.body
    });

    await activeConnection.release();

    ctx.status = 201;
    ctx.body = {
        data: 'Study updated'
    };
}

/**
 * Delete single user by ID
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function deleteStudy(ctx, next) {
    const activeConnection = await db.connect();

    const study = await studies.find({
        id: ctx.params.id
    });

    if (study.length == 0) {
        await activeConnection.release();
        ctx.throw(404, 'Study not found!');
    }

    await studies.delete(ctx.params.id);

    await activeConnection.release();

    ctx.status = 201;
    ctx.body = {
        data: 'Study deleted'
    };
}
