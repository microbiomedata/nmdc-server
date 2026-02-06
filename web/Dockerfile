FROM node:lts AS build-stage

# Define a "build argument" (i.e. a build-time parameter), which can be set via
# the `--build-arg KEY=VALUE` argument to the `$ docker build` command.
# Docs: https://docs.docker.com/build/building/variables/#arg-usage-example
ARG VITE_APP_NMDC_GOOGLE_ANALYTICS_ID=""

# Define an environment variable within the container image, whose value is
# the one passed in via the "build argument" defined above.
# Docs: https://docs.docker.com/build/building/variables/#env-usage-example
ENV VITE_APP_NMDC_GOOGLE_ANALYTICS_ID=${VITE_APP_NMDC_GOOGLE_ANALYTICS_ID}

ENV NODE_OPTIONS=--openssl-legacy-provider
WORKDIR /app
COPY package*.json yarn.lock ./
RUN yarn install
COPY . .
RUN yarn run build


FROM nginx:1.28-alpine AS production-stage
LABEL org.opencontainers.image.source=https://github.com/microbiomedata/nmdc-server

RUN rm -v /etc/nginx/nginx.conf
ADD nginx.conf.template /etc/nginx/
ADD start.sh /app/start.sh
RUN chmod +x /app/start.sh
COPY --from=build-stage /app/dist /www/data
EXPOSE 80
CMD /app/start.sh
