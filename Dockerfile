FROM debian:bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        unzip \
        python3 \
        python3-venv \
        python3-pip \
        supervisor \
    && rm -rf /var/lib/apt/lists/*

ARG XRAY_VERSION=1.8.24
RUN curl -fsSL -o /tmp/xray.zip "https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-64.zip" \
    && unzip -q /tmp/xray.zip -d /tmp/xray \
    && install -m 0755 /tmp/xray/xray /usr/local/bin/xray \
    && mkdir -p /usr/local/share/xray \
    && install -m 0644 /tmp/xray/geoip.dat /usr/local/share/xray/geoip.dat \
    && install -m 0644 /tmp/xray/geosite.dat /usr/local/share/xray/geosite.dat \
    && rm -rf /tmp/xray /tmp/xray.zip

RUN useradd -r -s /usr/sbin/nologin xrayapi \
    && mkdir -p /app /etc/xray /var/lib/xray-api \
    && chown -R xrayapi:xrayapi /app /var/lib/xray-api

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /app/venv \
    && /app/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

COPY xray_api /app/xray_api
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8585

ENV XRAY_API_DB_PATH=/var/lib/xray-api/xray.db \
    XRAY_CONFIG_PATH=/etc/xray/config.json

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
