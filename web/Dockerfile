FROM node:lts as build-stage
ENV NODE_OPTIONS=--openssl-legacy-provider
WORKDIR /app
COPY package*.json yarn.lock ./
RUN yarn install
COPY . .
RUN yarn run build


FROM nginx:1.28-alpine as production-stage
LABEL org.opencontainers.image.source=https://github.com/microbiomedata/nmdc-server

RUN rm -v /etc/nginx/nginx.conf
ADD nginx.conf.template /etc/nginx/
ADD start.sh /app/start.sh
RUN chmod +x /app/start.sh
COPY --from=build-stage /app/dist /www/data
EXPOSE 80
CMD /app/start.sh
