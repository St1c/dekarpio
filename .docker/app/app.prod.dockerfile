# Stage 1: Compile and Build angular codebase

# Use official node image as the base image
FROM node:lts as build

RUN mkdir /home/node/app && chown node:node /home/node/app
RUN mkdir /home/node/app/node_modules && chown node:node /home/node/app/node_modules
WORKDIR  /home/node/app

# Install all the dependencies
COPY ./app/package*.json .
RUN npm ci --force

# Add the source code to app
COPY ./app/ ./

# Generate the build of the application
ENV NODE_OPTIONS=--openssl-legacy-provider
RUN npm run build
USER node

# Stage 2: Serve app with nginx server

# Use official nginx image as the base image
FROM nginx:latest

# Change nginx port
ADD .docker/app.vhosts.prod.conf /etc/nginx/nginx.conf

# Copy the build output to replace the default nginx contents.
COPY --from=build /home/node/app/dist/dekarpio /usr/share/nginx/html

# Expose port 8080
EXPOSE 4201
