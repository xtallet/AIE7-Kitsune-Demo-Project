# === STAGE 1: Builder ========================================================
FROM rayproject/ray:2.32.0-py311-cpu AS builder

# Establecer usuario root para instalaciones
USER root

# Instalar compiladores, herramientas y UV (sin modificar PATH)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3-dev curl ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    curl -LsSf https://astral.sh/uv/install.sh | XDG_BIN_HOME=/usr/local/bin UV_NO_MODIFY_PATH=1 sh

# Asegurar que uv esté en el PATH
ENV PATH="/usr/local/bin:$PATH"

# Directorio de trabajo
WORKDIR /server_app

# Copiar archivos de dependencias
COPY pyproject.toml uv.lock* requirements.txt ./

# Use pyproject.toml to specify versions and avoid conflicts
# Fijar setuptools compatible y eliminar distutils (previene errores con Guardrails)
RUN rm -rf /usr/lib/python3.11/distutils /home/ray/anaconda3/lib/python3.11/distutils

# Instalar dependencias principales y de desarrollo
RUN uv pip install --system --prerelease=allow -r requirements.txt

# Crear carpeta para logs y ajustar permisos
RUN mkdir -p /home/ray/.guardrails/logs && chown ray:users /home/ray/.guardrails/logs

# Configurar token e instalar validador Guardrails (se puede usar en tiempo de build si el token se pasa como ARG)
ARG GUARDRAILS_HUB_TOKEN
RUN yes | guardrails configure --token "$GUARDRAILS_HUB_TOKEN" && \
    guardrails hub install hub://tryolabs/restricttotopic || \
    (echo "ERROR EN LA INSTALACIÓN DEL VALIDATOR, logs:" && cat /home/ray/.guardrails/logs/guardrails.log && exit 1)

# Limpieza profunda de cachés, pyc y __pycache__ para reducir tamaño de builder
RUN find /home/ray/anaconda3/lib/python3.11/site-packages -type d -name "__pycache__" -exec rm -rf {} + && \
    find /home/ray/anaconda3/lib/python3.11/site-packages -type f -name "*.pyc" -delete && \
    rm -rf /home/ray/anaconda3/lib/python3.11/site-packages/*.egg-info

# === STAGE 2: Final image ====================================================
FROM rayproject/ray:2.32.0-py311-cpu AS cbot_server

# Establecer usuario root para copiar e instalar
USER root

# Directorio de trabajo
WORKDIR /server_app

# Copiar binarios mínimos necesarios
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /home/ray/anaconda3/bin/guardrails /usr/local/bin/guardrails

# Asegurar PATH actualizado
ENV PATH="/usr/local/bin:$PATH"

# Copiar solo site-packages necesarios (no todo anaconda3)
COPY --from=builder /home/ray/anaconda3/lib/python3.11/site-packages \
                    /home/ray/anaconda3/lib/python3.11/site-packages

# Copiar aplicación y dependencias
COPY --from=builder /server_app /server_app

# Copiar código fuente adicional si no estaba ya en el builder
COPY app /server_app/app

# Limpieza adicional
RUN rm -rf /home/ray/.cache /root/.cache /tmp/*

# Cambiar al usuario no root
USER ray
WORKDIR /server_app/app
