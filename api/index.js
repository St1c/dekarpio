require('dotenv').config();
var path = require('path');
global.appRoot = path.resolve(__dirname);

const Koa = require('koa');
// const IO = require('koa-socket-2');
var bodyParser = require('koa-bodyparser');

const catchErrors = require('./middlewares/catch-errors.middleware');
const cors = require('./middlewares/cors');
const logger = require('./middlewares/logger.middleware');
const responseTimer = require('./middlewares/response-timer.middleware');
const router = require('./routes/index');

const app = new Koa();
const PORT = process.env.APP_PORT || 3000;
const HOST = process.env.APP_HOST || '0.0.0.0';

// Default error handler
app.use(catchErrors(async (ctx, next) => await next()));

// Logging for development
if (process.env.APP_ENV === 'development') {
    app
        .use(logger)
        .use(responseTimer);
}

// Main app middlewares
app
    .use(bodyParser(
        {
            maxBodySize: '10mb',
            formLimit: '10mb', // default is 56kb, increased for large JSON files
        }
    ))
    .use(cors)
    .use(router.routes())
    .use(router.allowedMethods());

// Exporting server for use in tests
const server = app.listen(PORT, HOST);

module.exports = server;