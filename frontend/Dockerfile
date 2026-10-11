FROM node:20-slim AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci
COPY . ./
RUN npx ng build --configuration=production

FROM nginx:1.27-alpine
COPY --from=build /web/dist/console/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
