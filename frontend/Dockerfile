FROM node:20-alpine

# I am setting up our working directory within the container.
WORKDIR /app

# I'm copying the package files separately to speed up the build process 
# by caching the node_modules layer.
COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

# I've set this up to run in development mode by default.
CMD ["npm", "run", "dev"]