FROM nginx:alpine

# Copy SPA assets
COPY index.html /usr/share/nginx/html/index.html

# Use SPA-friendly nginx config (listens on 8080 and injects env.js)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Entrypoint generates env.js from $OMNI_API_BASE at runtime
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

CMD ["/entrypoint.sh"]
