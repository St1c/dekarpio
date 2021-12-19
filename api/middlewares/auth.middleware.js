// Custom 401 handling if you don't want to expose koa-jwt errors to users
module.exports = (ctx, next) => {
    return next().catch((err) => {
        if (401 == err.status) {
            ctx.status = 401;
            ctx.body = 'Protected resource\n';
        } else {
            throw err;
        }
    });
}