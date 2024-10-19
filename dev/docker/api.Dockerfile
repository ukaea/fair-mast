FROM python:3.11
WORKDIR /code

RUN pip install uv

COPY pyproject.toml /code/pyproject.toml

RUN uv pip install . --system

COPY ./src /code/src

ENTRYPOINT ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "80"]
