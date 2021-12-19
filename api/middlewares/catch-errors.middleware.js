var fs = require('fs');
var util = require('util');
var log_file = fs.createWriteStream(appRoot + '/debug.log', {
    flags: 'w'
});
var log_stdout = process.stdout;

console.error = function (d) { //
    log_file.write(util.format(d) + '\n');
    log_stdout.write(util.format(d) + '\n');
};

module.exports = fn => (ctx, next) => 
    fn(ctx, next)
    .catch(err => {
        const message = err.message || err.sqlMessage || 'Uknown error';
        console.error('Handled error: ' + new Date().toISOString() + ' ' + message);

        ctx.status = err.statusCode || err.status || 500;
        ctx.body = {
            error: message
        };
    });