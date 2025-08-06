FROM astral/uv:bookworm-slim

WORKDIR /code

COPY pyproject.toml /code/pyproject.toml

RUN uv sync

COPY ./docs/built_docs/ /code/docs/built
COPY ./docs/default_docs/ /code/docs/default

ENV PATH="/code/.venv/bin:$PATH"

ENTRYPOINT ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "80"]