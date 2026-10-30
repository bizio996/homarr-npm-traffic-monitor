FROM python:3.12-alpine
RUN addgroup -S collector && adduser -S collector -G collector
WORKDIR /app
COPY collector.py /app/collector.py
USER collector
EXPOSE 8787
CMD ["python", "/app/collector.py"]
