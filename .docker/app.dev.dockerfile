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

RUN mkdir /opt/app && chown node:node /opt/app
WORKDIR /opt/app

# RUN mkdir -p /opt/app/src && chown node:node /opt/app/src
# WORKDIR /opt/app/src

# the official node image provides an unprivileged user as a security best practice
# but we have to manually enable it. We put it here so npm installs dependencies as the same
# user who runs the app. 
# https://github.com/nodejs/docker-node/blob/master/docs/BestPractices.md#non-root-user
# USER node
COPY ./app/package.json ./app/package-lock.json ./
RUN npm install
ENV PATH /opt/app/node_modules/.bin:$PATH
# ENV PATH /opt/app/src/node_modules/.bin:$PATH

# Create app source files directory
WORKDIR /opt/app/src
COPY ./app /opt/app/src

EXPOSE 3006

### Enter docker app container:
### docker-compose exec app /bin/sh
### From container run tests:
### npm run test
### Or run tests directly from host:
### docker-compose exec app yarn run test