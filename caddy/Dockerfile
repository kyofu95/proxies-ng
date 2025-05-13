FROM caddy:2.10.0-builder AS caddy-build 

RUN xcaddy build \
    --with github.com/mholt/caddy-ratelimit

FROM caddy:2.10.0-alpine AS caddy-final

COPY --from=caddy-build  /usr/bin/caddy /usr/bin/caddy