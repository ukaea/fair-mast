FROM python:3.11
WORKDIR /code

RUN pip install uv

COPY .docs/requirements.txt /code/requirements.txt

RUN uv pip install --system --no-cache -r /code/requirements.txt

COPY ./src /code/src

ENTRYPOINT ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "80"]
