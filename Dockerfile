FROM python:3.12-alpine AS build

ARG GIT_VERSION=2.47.2-r0
ARG CARGO_VERSION=1.83.0-r0
RUN apk upgrade --no-cache \
  && apk add --no-cache \
    git=$GIT_VERSION\
    cargo=$CARGO_VERSION

RUN --mount=type=bind,source=.,target=/src \
  --mount=type=tmpfs,target=/tmp/build \
  cp -R /src /tmp/build/yamlcrypt \
  && python -m venv /opt/yamlcrypt \
  && /opt/yamlcrypt/bin/pip install /tmp/build/yamlcrypt

FROM python:3.12-alpine

ARG LIBGCC_VERSION=14.2.0-r4
RUN apk upgrade --no-cache \
   && apk add --no-cache \
    libgcc=$LIBGCC_VERSION

COPY --from=build /opt/yamlcrypt /opt/yamlcrypt

ENTRYPOINT ["/opt/yamlcrypt/bin/yamlcrypt"]
