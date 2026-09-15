# Imagen base
FROM python:3.12-slim
# Evitar que python cree archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Permite visualizar los logs
ENV PYTHONBUFFERED=1
# Directorio de trabajo
WORKDIR /app
# Dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
# Dependencias de python
COPY requirements.txt .
# Instalamos las dependencias
RUN pip install --no-cache-dir -r requirements.txt
# Codigo de la aplicacion
COPY . .
# Puerto
EXPOSE 5000
# Ejecucion 
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers","3","run:app"]