FROM nginx:alpine

ADD .docker/certs/server.crt /etc/nginx/certs/server.crt
ADD .docker/certs/server.key /etc/nginx/certs/server.key

ADD .docker/nginx-conf/vhosts.prod.conf /etc/nginx/conf.d/default.conf
