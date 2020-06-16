FROM node:lts-alpine as build-stage
WORKDIR /app
COPY package*.json yarn.lock ./
RUN yarn install
COPY . .
RUN yarn run build

FROM nginx:stable-alpine as production-stage
RUN rm -v /etc/nginx/nginx.conf
ADD nginx.conf /etc/nginx/
COPY --from=build-stage /app/dist /www/data
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
