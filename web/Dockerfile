FROM node:lts as build-stage
ENV NODE_OPTIONS=--openssl-legacy-provider
WORKDIR /app
COPY package*.json yarn.lock ./
RUN yarn install
COPY . .
RUN yarn run build

# Previously, we rebuilt nginx from source to add the mod_zip module. This rebuild process stopped working when nginx
# shut down their Mercurial repo (used when building versions of nginx before 1.27) on April 17, 2025. However, using
# the mod_zip module requires us to stay on nginx 1.22.
#
# The long-term solution is to find an alternative to mod_zip.
#
# The short-term solution is to build the nmdc-server/client image off of the last stable version of the
# nmdc-server/client image (1.5.0). It has nginx 1.22.1 built with mod_zip already. Then we drop in the new
# frontend code.
FROM ghcr.io/microbiomedata/nmdc-server/client:1.5.0 as production-stage
LABEL org.opencontainers.image.source=https://github.com/microbiomedata/nmdc-server

ADD nginx.conf.template /etc/nginx/
ADD start.sh /app/start.sh
RUN chmod +x /app/start.sh
COPY --from=build-stage /app/dist /www/data
EXPOSE 80
CMD /app/start.sh
