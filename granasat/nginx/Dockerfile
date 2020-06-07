# Use the Nginx image
FROM arm32v7/nginx:1.18.0

# Remove the default nginx.conf
RUN rm /etc/nginx/conf.d/default.conf

# Add a favicon
ADD favicon.ico /favicon.ico

# Replace with our own nginx.conf
COPY nginx.conf /etc/nginx/conf.d/
