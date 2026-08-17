# Start with a small Linux image that already has Python 3.12
FROM python:3.12-slim


# Python settings for clean container logs
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1


# dbt inside Docker uses the project-level profile
ENV DBT_PROFILES_DIR=/app/dbt

# Docker uses dbt Core + dbt-bigquery
ENV DBT_EXECUTABLE=dbt


# Give Dagster a runtime home inside the container
ENV DAGSTER_HOME=/app/.dagster_runtime


# Everything inside the container lives here
WORKDIR /app


# Install system dependencies needed by dbt
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*


# Copy dependency list first for Docker layer caching
COPY requirements.txt .


# Install Python dependencies
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt


# Copy the project into the container
COPY . .


# Generate dbt's manifest inside the container.
#
# dbt/target is intentionally not copied from the host,
# so this image is reproducible from a fresh Git checkout.
RUN dbt parse \
    --project-dir /app/dbt \
    --profiles-dir /app/dbt


# Create Dagster runtime directory and disable telemetry
RUN mkdir -p "$DAGSTER_HOME" \
    && printf "telemetry:\n  enabled: false\n" \
    > "$DAGSTER_HOME/dagster.yaml"


# Starting the container runs the full pipeline once
CMD ["dg", "launch", "--job", "__ASSET_JOB"]