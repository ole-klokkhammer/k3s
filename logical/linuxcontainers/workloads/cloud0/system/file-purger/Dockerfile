FROM alpine:3.18
RUN apk add --no-cache bash findutils
COPY ./src/purge.sh /usr/local/bin/purge.sh
ENTRYPOINT ["/usr/local/bin/purge.sh"]