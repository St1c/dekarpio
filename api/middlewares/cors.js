module.exports = cors;

async function cors(ctx, next) {
    ctx.set("Access-Control-Allow-Origin", "*");
    ctx.set("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization");
    if (ctx.method === 'OPTIONS') {
        ctx.set('Access-Control-Allow-Methods', 'PUT, POST, PATCH, DELETE, GET');
        ctx.status = 200;
    }
    await next();
}