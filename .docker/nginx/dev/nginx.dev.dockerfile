FROM nginx:alpine

ADD .docker/nginx/dev/vhosts.dev.conf /etc/nginx/conf.d/default.conf
