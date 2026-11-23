FROM --platform=$BUILDPLATFORM python:3.12-slim AS deps
WORKDIR /app
RUN pip install --no-cache-dir poetry==2.1.3 poetry-plugin-export==1.9.0
COPY pyproject.toml poetry.lock ./
RUN poetry export --only main --without-hashes --output requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=deps /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

RUN useradd --create-home --uid 1000 module \
    && mkdir -p /data && chown module:module /data
USER module

CMD ["python", "main.py"]
