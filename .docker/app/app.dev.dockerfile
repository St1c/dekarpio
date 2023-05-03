FROM node:18.15.0
RUN mkdir /home/node/app && chown node:node /home/node/app
RUN mkdir /home/node/app/node_modules && chown node:node /home/node/app/node_modules
WORKDIR  /home/node/app
#USER node

COPY --chown=node:node ./app/package.json ./app/package-lock.json ./
RUN npm cache clean --force
RUN npm ci force
COPY --chown=node:node ./app .