FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3 python3-numpy python3-pil python3-pikepdf python3-img2pdf \
      python3-requests tini tzdata \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY deskew.py deskew_hook.py service.py entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh /app/deskew_hook.py /app/service.py \
 && python3 -c "import deskew, service"

ENTRYPOINT ["/usr/bin/tini", "--", "/app/entrypoint.sh"]
