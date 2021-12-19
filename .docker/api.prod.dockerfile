FROM node:10-alpine

RUN apk --no-cache add --virtual native-deps \
    g++ gcc libgcc libstdc++ linux-headers autoconf automake make nasm python git && \
    npm install --quiet node-gyp -g

RUN npm install pm2 -g

# Create app directory
WORKDIR /var/www/api

### install node_modules in container - do not use the local one:
### bcrypt needs to be build and compiled for targeted system  because it uses native libs!!!
COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3001

CMD [ "npm", "run", "start:pm2" ]