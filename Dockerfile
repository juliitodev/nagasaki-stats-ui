FROM python:3.12-slim

WORKDIR /project
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY scripts ./scripts
RUN chmod +x scripts/docker-entrypoint.sh

ENV FLASK_APP=src.app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=3080
EXPOSE 3080

ENTRYPOINT ["/project/scripts/docker-entrypoint.sh"]
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=3080"]
