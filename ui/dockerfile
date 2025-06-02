FROM node:18.19.0-alpine

EXPOSE 3000

COPY . /ui
WORKDIR /ui

RUN npm i
RUN npm run build

ENTRYPOINT [ "npm", "start" ]
