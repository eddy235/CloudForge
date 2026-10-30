# CloudForge v0.1 - reproducible, read-only NexusDesk demo image.
# The upstream code is checked out at the pinned commit in upstream/NexusDesk.
# Pin this image to a reviewed digest for stricter production supply-chain controls.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /opt/nexusdesk
RUN groupadd --system app && useradd --system --gid app --home-dir /opt/nexusdesk app

COPY upstream/NexusDesk/requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt && python -m pip check
COPY upstream/NexusDesk/ ./

# Static build has no secrets and does not provision a database.
RUN DJANGO_DEBUG=true python manage.py collectstatic --noinput \
    && mkdir -p /opt/nexusdesk/staticfiles \
    && chown -R app:app /opt/nexusdesk

USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/', timeout=3)"

# Do not enable the operational helpdesk on the public CloudForge deployment.
CMD ["gunicorn", "nexusdesk.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--access-logfile", "-", "--error-logfile", "-"]
