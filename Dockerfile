# backend/Dockerfile

# Mulai dari "fondasi" kita yang sudah lengkap dan siap pakai
FROM fotota-backend-base:local-build

# Set working directory
WORKDIR /app

# Buat user non-root
RUN addgroup --system app && adduser --system --group app

# Definisikan Environment Variable untuk DeepFace
# Ini memberitahu DeepFace untuk menyimpan semua modelnya di /app/.deepface
ENV DEEPFACE_HOME=/app/.deepface

# Buat direktori-direktori yang kita butuhkan
# Termasuk direktori baru untuk DeepFace
RUN mkdir -p /app/logs \
    && mkdir -p /app/storage \
    && mkdir -p /app/.deepface

# Berikan kepemilikan SEMUA folder di /app kepada user 'app'
# Ini akan memastikan user 'app' punya izin menulis ke .deepface, logs, dan storage
RUN chown -R app:app /app

# Salin kode aplikasi Anda.
COPY ./app /app/app
COPY ./log_config.yaml /app/log_config.yaml
COPY ./storage/assets /app/assets

# Buat direktori logs dan storage
RUN mkdir -p /app/logs
RUN mkdir -p /app/storage

# Berikan kepemilikan ke user 'app'
RUN chown -R app:app /app

# Ganti ke user non-root
USER app

# Expose port
EXPOSE 8000

# Perintah untuk menjalankan aplikasi
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]