# Use an official Node.js runtime as a parent image
FROM node:18

# Set the working directory
WORKDIR /usr/src/app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install dependencies
RUN npm install

# Install yt-dlp (a YouTube downloader)
RUN apt-get update && apt-get install -y yt-dlp

# Copy the rest of the application code
COPY . .

# Expose the port for the app (adjust this if you use a different port)
EXPOSE 3000

# Start the application
CMD ["node", "api/ffprobe.js"]
