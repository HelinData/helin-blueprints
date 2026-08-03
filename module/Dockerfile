FROM python:3.12-slim 

WORKDIR /app

# Dependencies are pinned by poetry.lock; --only main keeps dev tools
# (pytest, linters, ...) out of the runtime image if you add them later.
RUN pip install --no-cache-dir poetry==2.1.3
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction

COPY main.py .

# Run as non-root. 
# /data is where the platform bind-mounts the config volume
RUN useradd --create-home --uid 1000 module \
    && mkdir -p /data && chown module:module /data
USER module

CMD ["python", "main.py"]
