FROM python:3.11
WORKDIR /code

ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

COPY ./requirements.txt /code/requirements.txt

RUN /root/.cargo/bin/uv pip install --system --no-cache -r /code/requirements.txt

COPY ./src /code/src

ENTRYPOINT ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "80"]
