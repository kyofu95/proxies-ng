FROM python:3.12.9-slim AS python-base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV POETRY_HOME="/opt/poetry" \
    # make poetry create the virtual environment in the project's root
    # it gets named `.venv`
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=2.1.0 \
    # paths
    # this is where our requirements + virtual environment will live
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# BUILD

FROM python-base AS build

RUN apt-get update

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
ADD "https://install.python-poetry.org" /tmp/get-poetry.py
RUN python3 /tmp/get-poetry.py


# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry install --no-root --no-interaction

# FINAL

FROM python-base AS final

WORKDIR $PYSETUP_PATH

# copy in our built poetry + venv
COPY --from=build $POETRY_HOME $POETRY_HOME
COPY --from=build $PYSETUP_PATH $PYSETUP_PATH

# quicker install as runtime deps are already installed
RUN poetry install --no-root

# will become mountpoint of our code
WORKDIR /fastapi_project

# fastapi app
COPY app app

# alembic files
COPY migrations migrations
COPY alembic.ini .

COPY entrypoint.sh entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]