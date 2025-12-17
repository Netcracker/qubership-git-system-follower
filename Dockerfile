ARG APPDIR=/app
ARG VENV=${APPDIR}/.venv


FROM debian:trixie-slim AS git-builder
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /git-deps \
    && ldd "$(which git)" \
    | tr -s '[:blank:]' '\n' \
    | grep '^/' \
    | sort -u \
    | xargs -I '{}' cp --parents '{}' /git-deps


FROM ghcr.io/astral-sh/uv:trixie-slim AS builder
ARG APPDIR
ARG VENV

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_INSTALL_DIR=/python \
    UV_PYTHON_PREFERENCE=only-managed

RUN --mount=type=bind,source=.python-version,target=.python-version \
    uv python install
    # && find /python -name '*.a' -delete \
    # && find /python -name '*.pdb' -delete \
    # && find /python -name '*.dbg' -delete \
    # && rm -rf /python/cpython-*/include /python/cpython-*/share

# RUN PYTHON_DIR=$(ls -d /python/cpython-*) \
#     && rm -rf "$PYTHON_DIR"/lib/python*/test \
#               "$PYTHON_DIR"/lib/python*/idlelib \
#               "$PYTHON_DIR"/lib/python*/tkinter \
#               "$PYTHON_DIR"/lib/python*/ensurepip \
#               "$PYTHON_DIR"/lib/python*/site-packages \

#               "$PYTHON_DIR"/lib/itcl* \
#               "$PYTHON_DIR"/lib/tcl* \
#               "$PYTHON_DIR"/lib/tk* \
#               "$PYTHON_DIR"/lib/thread* \

#               "$PYTHON_DIR"/bin/idle3* \
#               "$PYTHON_DIR"/bin/pydoc3* \
#               "$PYTHON_DIR"/bin/pip* \
#               "$PYTHON_DIR"/bin/python*-config

WORKDIR ${APPDIR}
COPY git_system_follower/ ${APPDIR}/git_system_follower
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=README.md,target=${APPDIR}/README.md \
    --mount=type=bind,source=pyproject.toml,target=${APPDIR}/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=${APPDIR}/uv.lock \
    uv sync --locked --no-dev --no-editable --no-install-project
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=README.md,target=${APPDIR}/README.md \
    --mount=type=bind,source=pyproject.toml,target=${APPDIR}/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=${APPDIR}/uv.lock \
    uv sync --locked --no-dev --no-editable

# RUN find "${VENV}"/lib/python*/site-packages -name "*.py" -delete
# RUN find "${VENV}"/lib/python*/site-packages -type d -name "__pycache__" -print0 | xargs -0 -I {} /bin/rm -rf "{}"


# FROM debian:trixie-slim
FROM gcr.io/distroless/cc-debian13:nonroot
ARG APPDIR
ARG VENV

COPY --from=git-builder /usr/bin/git /usr/bin/git
COPY --from=git-builder /usr/lib/git-core /usr/lib/git-core
COPY --from=git-builder /git-deps /usr

COPY --from=builder /python /python
# COPY --from=builder /python-deps /usr

COPY --from=builder --chown=nonroot:nonroot ${VENV} ${VENV}
COPY --from=builder --chown=nonroot:nonroot ${APPDIR} ${APPDIR}

ENV PATH="${VENV}/bin:${PATH}"
WORKDIR ${APPDIR}

CMD ["gsf"]