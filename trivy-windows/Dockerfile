FROM aquasec/trivy:latest AS scanner
FROM python:3.12-slim
COPY --from=scanner /usr/local/bin/trivy /usr/local/bin/trivy
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd -m scanner && mkdir -p /home/scanner/.cache/trivy && chown -R scanner:scanner /home/scanner
COPY --chown=scanner:scanner . .
USER scanner
ENV TRIVY_CACHE_DIR=/home/scanner/.cache/trivy
EXPOSE 8080
CMD ["gunicorn","--workers","1","--threads","4","--timeout","240","--bind","0.0.0.0:8080","app:app"]
