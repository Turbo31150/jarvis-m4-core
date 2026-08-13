FROM jarvis-antigravity-mcp:latest

# Install bash + curl (needed by antigravity-ask.sh) — image is node:alpine-like
USER root
RUN (apk add --no-cache bash curl jq 2>/dev/null) || (apt-get update && apt-get install -y --no-install-recommends bash curl jq && rm -rf /var/lib/apt/lists/*) || true

# Bake the antigravity-ask.sh script into the image so the container is self-contained
COPY antigravity-ask.sh /usr/local/bin/antigravity-ask.sh
RUN chmod +x /usr/local/bin/antigravity-ask.sh

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENV ANTIGRAV_SCRIPT=/usr/local/bin/antigravity-ask.sh
ENV PORT=8902

COPY healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
