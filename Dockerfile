FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FITLIFE_RUNTIME=huggingface \
    PORT=7860

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 user \
    && mkdir -p /home/user/app \
    && chown -R user:user /home/user

USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user:user requirements-space.txt ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-space.txt

COPY --chown=user:user gateway ./gateway
COPY --chown=user:user services ./services
COPY --chown=user:user data/nutri-ai ./data/nutri-ai
COPY --chown=user:user model/models ./model/models

EXPOSE 7860

CMD ["python", "gateway/app.py"]
