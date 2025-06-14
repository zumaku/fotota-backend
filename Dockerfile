# backend/Dockerfile

# Mulai dari "fondasi" kita yang sudah lengkap dan siap pakai
FROM fotota-backend-base:local-build

# Set working directory
WORKDIR /app

# Buat user non-root
RUN addgroup --system app && adduser --system --group app

# Salin kode aplikasi Anda.
COPY ./app /app/app
COPY ./log_config.yaml /app/log_config.yaml

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