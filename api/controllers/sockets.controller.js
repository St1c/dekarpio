module.exports.index = index;
module.exports.onFilterChange = onFilterChange;
module.exports.onFilterReset = onFilterReset;
module.exports.onFilterActiveSectionChange = onFilterActiveSectionChange;
module.exports.onMessage = onMessage;
module.exports.setupIOListeners = setupIOListeners;

function setupIOListeners(io) {
    io.on('connection', socket => {
        console.log(socket.handshake.query)
        socket.join(socket.handshake.query.userId);
        console.log(socket.rooms)
    });
    io.on('disconnect', socket => console.log('socket disconnected'));
    io.on('message', onMessage);
    io.on('enableFilters', onEnableFilters);
    io.on('filterChange', onFilterChange);
    io.on('filterReset', onFilterReset);
    io.on('filterActiveSectionChange', onFilterActiveSectionChange);
}

async function index(ctx, next, io) {
    console.log('socket controller middleware example');
    await next();
}

function onMessage(ctx, data) {
    console.log('Message received', data);
}

function onEnableFilters(ctx, data) {
    console.log('filter enable/disable received: ', data);
    ctx.socket.broadcast.to(data.userId).emit('enableFilters', data.value);
}

function onFilterChange(ctx, data) {
    console.log('filter change received: ', data);
    ctx.socket.broadcast.to(data.userId).emit('changeFilter', data.filterValue);
}

function onFilterReset(ctx, data) {
    console.log('filter reset received: ', data);
    ctx.socket.broadcast.to(data.userId).emit('resetFilter', data.filterReset);
}

function onFilterActiveSectionChange(ctx, data) {
    console.log('filter active section change received: ', data);
    ctx.socket.broadcast.to(data.userId).emit('changeFilterActiveSection', data.section);
}