const performance = require('perf_hooks').performance;

module.exports = async (ctx, next) => {
    const start = performance.now();
    await next();
    const ms = Math.round(1000 * (performance.now() - start)) / 1000;
    ctx.set('X-Response-Time', `${ms}ms`);
}