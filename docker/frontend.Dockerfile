FROM nginx:alpine

COPY website/ /usr/share/nginx/html/
COPY widget/widget.js widget/widget.css /usr/share/nginx/html/widget/
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Inside the container, the browser uses the same origin and Nginx proxies /api to FastAPI.
RUN find /usr/share/nginx/html -type f -name '*.html' \
    -exec sed -i 's|data-api-url="http://127.0.0.1:8000"|data-api-url=""|g' {} +

EXPOSE 80
