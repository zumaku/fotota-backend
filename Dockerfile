# backend/Dockerfile

# Mulai dari "fondasi" yang sudah kita buat secara lokal
FROM fotota-backend-base:local-build

# Mengatur working directory di dalam container
WORKDIR /app

# Membuat user non-root untuk keamanan
RUN addgroup --system app && adduser --system --group app

# Menyalin kode aplikasi Anda. Tidak ada lagi 'pip install' di sini!
COPY ./app /app/app
COPY ./log_config.yaml /app/log_config.yaml
RUN mkdir -p /app/logs && chown -R app:app /app/logs
RUN mkdir -p /app/storage && chown -R app:app /app/storage
COPY ./storage/events/no_image.png /app/storage/events/no_image.png
RUN chown -R app:app /app

# Ganti ke user non-root
USER app

# Expose port
EXPOSE 8000

# Perintah untuk menjalankan aplikasi
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]