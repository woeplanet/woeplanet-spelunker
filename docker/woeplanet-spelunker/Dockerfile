ARG DEBIAN_RELEASE=invalid
ARG VERSION=invalid

FROM debian:${DEBIAN_RELEASE} AS build
ARG DEBIAN_RELEASE
ARG VERSION

### --------------------------------------------------------------------------------
### Start - build prep

SHELL ["/bin/sh", "-exc"]
ENV DEBIAN_FRONTEND=noninteractive

# - install OpenSSH and Python 3

RUN <<EOT
apt-get update -qy
apt-get install -qyy \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    openssh-client \
    python3
EOT

# - install uv, but just for this layer
COPY --from=ghcr.io/astral-sh/uv:0.9.21 /uv /usr/local/bin/uv

# - copy instead of hard linking (which uv will complain about)
# - don't (yet) compile to bytecode after installation for faster startup times
# - don't (yet) do concurrent builds
#   follow https://github.com/astral-sh/uv/issues/6105 for if/when it's resolved
# - use the just installed Python version and don't (un-helpfully) download one
# - tell uv which Python binary to use
# - tell uv sync where to sync to

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_CONCURRENT_INSTALLS=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=/usr/bin/python3.13 \
    UV_PROJECT_ENVIRONMENT=/opt/woeplanet

### End - build prep

### --------------------------------------------------------------------------------
### Start - dependencies prep

# - install runtime dependencies only, without the application itself
# - this layer will be cached until either uv.lock or pyproject.toml
#   change, these are mounted here into the build layer as we
#   don't need them at runtime

RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=ssh <<EOT
mkdir -p "${HOME}"/.ssh
chmod 0600 "${HOME}"/.ssh
ssh-keyscan github.com >> "${HOME}"/.ssh/known_hosts
uv sync \
        --locked \
        --no-dev \
        --no-install-project
EOT

# - install everything else (the application itself), without dependencies
# - /src is temporary to this layer and won't be copied into the runtime layer

COPY . /src
WORKDIR /src

RUN --mount=type=cache,target=/root/.cache \
    uv sync \
        --locked \
        --no-dev \
        --no-editable

### End - dependencies prep

### --------------------------------------------------------------------------------
### Start - runtime

FROM debian:${DEBIAN_RELEASE}
ARG DEBIAN_RELEASE
ARG VERSION

SHELL ["/bin/sh", "-exc"]
ENV DEBIAN_FRONTEND=noninteractive

# - don't run as root
RUN <<EOT
groupadd --system woeplanet
useradd --system --home-dir /opt/woeplanet --gid woeplanet --no-user-group woeplanet
EOT

# - setup runtime search paths

ENV PYTHONPATH=/opt/woeplanet
ENV PATH=/opt/woeplanet/bin:${PATH}
ENV VIRTUAL_ENV=/opt/woeplanet
ENV WOEPLANET_ROOT=/opt/woeplanet

# - install curl for health checks
# - install Python 3 without installer or development tools
# - install tini as a container init to allow signals to be correctly propagated

RUN <<EOT
apt-get update -qy
apt-get install -qyy \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    ca-certificates \
    curl \
    libsqlite3-mod-spatialite \
    python3 \
    tini
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOT

COPY --from=build --chown=woeplanet:woeplanet /opt/woeplanet /opt/woeplanet
COPY --chown=woeplanet:woeplanet ./docker/woeplanet-spelunker/files/docker-entrypoint.sh /opt/woeplanet/
COPY --chown=woeplanet:woeplanet ./config/logging.yml /opt/woeplanet/config/logging.yml
COPY --chown=woeplanet:woeplanet ./static /opt/woeplanet/static
COPY --chown=woeplanet:woeplanet ./templates /opt/woeplanet/templates

WORKDIR /opt/woeplanet
EXPOSE 80
ENTRYPOINT ["/usr/bin/tini", "-v", "--", "/opt/woeplanet/docker-entrypoint.sh"]
CMD ["server"]
STOPSIGNAL SIGINT
# HEALTHCHECK CMD curl --silent --fail http://localhost:80/health || exit 1

LABEL org.opencontainers.image.url="https://github.com/woeplanet/woeplanet-spelunker"
LABEL org.opencontainers.image.documentation="https://github.com/woeplanet/woeplanet-spelunker/blob/master/README.md"
LABEL org.opencontainers.image.source="https://github.com/woeplanet/woeplanet-spelunker"
LABEL org.opencontainers.image.version=${VERSION}
LABEL org.opencontainers.image.revision=${VERSION}
LABEL org.opencontainers.image.vendor="WOEplanet"
LABEL org.opencontainers.image.licenses="BSD-3-Clause"
LABEL org.opencontainers.image.title="The WOEplanet Spelunker"
LABEL org.opencontainers.image.description="The WOEplanet Spelunker"
LABEL org.opencontainers.image.base.name=docker.io/debian:${DEBIAN_RELEASE}

### End - runtime

### --------------------------------------------------------------------------------
### Start - smoke test

# - check that the installed Python version is what we expect
# - check that one of the dependencies can be imported
# - check that what we've installed can actually be imported

RUN <<EOT
python3 --version
python3 -Ic 'import uvicorn'
#python3 -Ic 'import woeplanet.spelunker.server'
EOT

### End - smoke test
