# === STAGE 1: Builder ========================================================
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3-dev curl ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    curl -LsSf https://astral.sh/uv/install.sh | XDG_BIN_HOME=/usr/local/bin UV_NO_MODIFY_PATH=1 sh

ENV PATH="/usr/local/bin:$PATH"
WORKDIR /server_app

COPY pyproject.toml uv.lock* requirements.txt ./

RUN uv pip install --system --prerelease=allow -r requirements.txt

ARG GUARDRAILS_HUB_TOKEN
RUN yes | guardrails configure --token "$GUARDRAILS_HUB_TOKEN" && \
    guardrails hub install hub://tryolabs/restricttotopic || \
    (echo "ERROR INSTALLING VALIDATOR, logs:" && cat /root/.guardrails/logs/guardrails.log && exit 1)

RUN find /usr/local/lib/python3.12/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.12/site-packages -type f -name "*.pyc" -delete && \
    rm -rf /usr/local/lib/python3.12/site-packages/*.egg-info

# === STAGE 2: Final image ====================================================
FROM python:3.12-slim AS chatbot_server

WORKDIR /server_app

COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /usr/local/bin/guardrails /usr/local/bin/guardrails

ENV PATH="/usr/local/bin:$PATH"

COPY --from=builder /usr/local/lib/python3.12/site-packages \
                    /usr/local/lib/python3.12/site-packages

COPY --from=builder /server_app /server_app
COPY app /server_app/app
COPY run_server.py /server_app/

RUN rm -rf /root/.cache /tmp/*

RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /server_app

USER appuser

WORKDIR /server_app

EXPOSE 8000

CMD ["python", "run_server.py", "--host", "0.0.0.0", "--port", "8000"]
