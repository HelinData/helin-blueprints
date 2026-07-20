# Sample module container (User Story 24552).
# Requirements: pinned dependencies (lockfile) and a non-root runtime user.
FROM python:3.12-slim

WORKDIR /app

# TODO(24552): pin helin-edge-sdk and all transitive deps in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Run as non-root
RUN useradd --create-home --uid 1000 module
USER module

CMD ["python", "main.py"]
