FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /entrypoint.sh
COPY templates /templates

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
