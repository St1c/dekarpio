FROM node:10-alpine

RUN apk --no-cache add --virtual native-deps \
    g++ gcc libgcc libstdc++ linux-headers autoconf automake make nasm python git && \
    npm install --quiet node-gyp -g

RUN npm install pm2 -g

### install node_modules in container - do not use the local one:
### bcrypt needs to be build and compiled for targeted system  because it uses native libs!!!
### Based on tutorial from: https://www.docker.com/blog/keep-nodejs-rockin-in-docker/
# install dependencies first, in a different location for easier app bind mounting for local development
# due to default /opt permissions we have to create the dir with root and change perms
RUN mkdir /opt/api && chown node:node /opt/api
WORKDIR /opt/api
# the official node image provides an unprivileged user as a security best practice
# but we have to manually enable it. We put it here so npm installs dependencies as the same
# user who runs the app. 
# https://github.com/nodejs/docker-node/blob/master/docs/BestPractices.md#non-root-user
USER node
COPY ./api/package.json ./
RUN npm install --no-optional && npm cache clean --force
ENV PATH /opt/api/node_modules/.bin:$PATH

# Create api source files directory
WORKDIR /opt/api/src
COPY ./api /opt/api/src

### Initialize DB with this command
### docker-compose exec api npm run db-migrate:up

### For testing DB run:
### docker-compose exec api npm run db-migrate:db:test
### docker-compose exec api npm run db-migrate:up:test

### For running tests (first create qoestream_test db) 
### Enter docker api container:
### docker-compose exec api /bin/sh
### From container run tests:
### npm run test
### Or run tests directly from host:
### docker-compose exec api yarn run test