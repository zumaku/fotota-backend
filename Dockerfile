# --- Stage 1: Build Stage ---
# Menggunakan image Python penuh untuk menginstal dependensi,
# termasuk yang mungkin memerlukan build tools.
FROM python:3.11-slim as builder

# Mengatur working directory di dalam container
WORKDIR /app

# Menginstal dependensi sistem jika diperlukan (misal: untuk postgresql client)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Menyalin hanya file requirements terlebih dahulu untuk memanfaatkan Docker cache
COPY requirements.txt .

# Menginstal dependensi
# --no-cache-dir untuk ukuran image yang lebih kecil
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


# --- Stage 2: Final Production Image ---
# Memulai dari base image yang lebih kecil (slim)
FROM python:3.11-slim

# Mengatur working directory yang sama
WORKDIR /app

# Membuat user non-root untuk keamanan
# Menjalankan container sebagai root adalah praktik yang buruk.
RUN addgroup --system app && adduser --system --group app

# Menyalin dependensi yang sudah terinstal dari stage builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Menyalin kode aplikasi
# Pastikan folder 'app', 'log_config.yaml', dan 'storage/events/no_image.png' ada
COPY ./app /app/app
COPY ./log_config.yaml /app/log_config.yaml
# Buat direktori logs dan storage agar user 'app' memiliki akses
RUN mkdir -p /app/logs && chown -R app:app /app/logs
RUN mkdir -p /app/storage/events && chown -R app:app /app/storage
# Salin placeholder image
COPY ./storage/events/no_image.png /app/storage/events/no_image.png

# Ganti kepemilikan semua file aplikasi ke user 'app'
RUN chown -R app:app /app

# Ganti ke user non-root
USER app

# Memberi tahu Docker bahwa container akan mendengarkan di port 8000
EXPOSE 8000

# Perintah untuk menjalankan aplikasi saat container dimulai
# Menggunakan array agar menjadi entrypoint utama.
# Tidak menggunakan --reload di produksi.
# Menggunakan host 0.0.0.0 agar bisa diakses dari luar container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "log_config.yaml"]