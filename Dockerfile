FROM python:3.12-alpine3.23 AS build

ARG GIT_VERSION=2.52.1-r0
ARG CARGO_VERSION=1.91.1-r2
RUN apk upgrade --no-cache \
  && apk add --no-cache \
    git=$GIT_VERSION\
    cargo=$CARGO_VERSION

RUN --mount=type=bind,source=.,target=/src \
  --mount=type=tmpfs,target=/tmp/build \
  cp -R /src /tmp/build/yamlcrypt \
  && python -m venv /opt/yamlcrypt \
  && /opt/yamlcrypt/bin/pip install /tmp/build/yamlcrypt

FROM python:3.12-alpine3.23
LABEL org.opencontainers.image.source=https://github.com/anotw/yamlcrypt
LABEL org.opencontainers.image.description="A simple CLI to encrypt data in yaml files"
LABEL org.opencontainers.image.licenses=MIT

ARG LIBGCC_VERSION=15.2.0-r2
RUN apk upgrade --no-cache \
   && apk add --no-cache \
    libgcc=$LIBGCC_VERSION

COPY --from=build /opt/yamlcrypt /opt/yamlcrypt

ENTRYPOINT ["/opt/yamlcrypt/bin/yamlcrypt"]
