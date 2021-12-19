const fs = require('fs');
const path = require('path');
var Unzipper = require("decompress-zip")
// const unzipper = require('unzipper');
// const fsPromises = fs.promises;

module.exports.uploadStudy = uploadStudy;

/**
 * Upload files to existing study
 *
 * @param {Object} ctx Request, response
 * @param {Object} next Next handler
 */
async function uploadStudy(ctx, next) {

    if (ctx.file){
        const uploadPath = path.resolve(__dirname, '../../data/studies/')
        const filepath = ctx.file.path;
        const unzipper = new Unzipper(filepath);

        unzipper.on("extract", () => console.log("Finished extracting"));
        unzipper.extract({ path: uploadPath});
    }

    ctx.status = 201;
    ctx.body = {
        data: 'File processed'
    };
}

