# Imagen base
FROM python:3.12-slim

# Evitar que python cree archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Permite visualizar los logs
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Dependencias de python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Codigo de la aplicacion (lo excluido está en .dockerignore)
COPY . .

# Ejecutar sin privilegios de root
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

# Puerto
EXPOSE 5000

# Ejecucion (sin --reload: imagen de producción)
# --max-requests recicla cada worker (evita fugas de memoria a largo plazo).
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--timeout", "60", "--max-requests", "1000", "--max-requests-jitter", "100", "--access-logfile", "-", "--error-logfile", "-", "run:app"]
