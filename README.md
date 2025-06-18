# Backend FotoTa - FastAPI

Selamat datang di repositori backend untuk aplikasi **FotoTa**. Proyek ini dibangun menggunakan FastAPI dan menyediakan serangkaian API yang kuat untuk mendukung aplikasi mobile pencarian foto berbasis pengenalan wajah.

## Tentang Proyek Ini

FotoTa adalah sebuah aplikasi yang bertujuan untuk mempermudah pengguna mencari foto diri mereka dari dokumentasi sebuah event. Admin (penyelenggara event) dapat membuat "folder" event, mengunggah ratusan foto, dan melindunginya dengan password. Pengguna kemudian dapat mengakses event tersebut dan menggunakan foto selfie mereka untuk secara ajaib menemukan semua foto yang mengandung wajah mereka.

Backend ini menangani semua logika bisnis, mulai dari autentikasi pengguna, manajemen event dan gambar, hingga menyediakan endpoint untuk fitur pencarian wajah.

## Fitur Utama ✨

  - **Autentikasi Modern**: Login sosial menggunakan Akun Google dengan alur *Server-Side Auth Code*.
  - **Sistem Token JWT**: Menggunakan *Access Token* (berlaku singkat) dan *Refresh Token* (berlaku lama) untuk sesi yang aman.
  - **Manajemen Peran**: Sistem peran sederhana untuk membedakan **Pengguna Biasa** dan **Admin**.
  - **Manajemen Event**: Admin dapat membuat, mencari, mengubah, dan menghapus event yang dilindungi password.
  - **Manajemen Gambar**: Endpoint untuk upload banyak gambar sekaligus ke sebuah event.
  - **Fitur Pengguna**:
      - Upload foto selfie sebagai referensi wajah.
      - Melihat riwayat event yang baru diakses.
      - Mem-bookmark foto favorit ke koleksi "Fotota".
      - Operasi bookmark dan hapus bookmark secara massal.
  - **Pencarian Wajah**: Endpoint khusus yang terintegrasi dengan `DeepFace` untuk mencari wajah pengguna di dalam sebuah event.
  - **Proses Latar Belakang**: Indexing wajah dilakukan sebagai *background task* agar tidak memblokir pengguna saat admin mengunggah foto.
  - **Logging Profesional**: Sistem logging terstruktur dengan warna untuk terminal dan rotasi file harian untuk produksi.

## Struktur Projek

Proyek ini disusun dengan memisahkan tanggung jawab untuk kemudahan pemeliharaan dan skalabilitas.

```

app/
├── api/          # Semua endpoint (routers) dan dependensi
├── core/         # Konfigurasi inti dan utilitas keamanan
├── crud/         # Fungsi interaksi database (Create, Read, Update, Delete)
├── db/           # Pengaturan koneksi dan model database SQLAlchemy
├── schemas/      # Skema Pydantic untuk validasi data
├── services/     # Logika bisnis kompleks (Google OAuth, Face Recognition)
└── main.py       # Titik masuk utama aplikasi FastAPI

```

## Prasyarat

  - Python 3.9+
  - PostgreSQL Server
  - `pip` untuk manajemen dependensi

## Instalasi & Konfigurasi

Ikuti langkah-langkah ini secara berurutan untuk menjalankan proyek.

### 1\. Kloning Repositori

```bash
git clone https://github.com/zumaku/fotota-backend
cd backend
```

### 2\. Konfigurasi Environment

Buat file `.env` di dalam direktori `backend/` dengan menyalin dari `.env.example` atau dari template di bawah ini. Isi semua nilainya sesuai dengan konfigurasi Anda.

**Template `.env`:**

```env
# Detail Proyek
PROJECT_NAME="FotoTa API"
PROJECT_VERSION="1.0.0"

# Base URL (PENTING untuk URL gambar yang benar)
# Untuk development, gunakan http://localhost:8000. Untuk produksi, gunakan domain publik Anda.
API_BASE_URL="http://localhost:8000"

# Kredensial Google OAuth (dari GCP, gunakan kredensial Tipe "Web application")
GOOGLE_CLIENT_ID="MASUKKAN_CLIENT_ID_WEB_ANDA"
GOOGLE_CLIENT_SECRET="MASUKKAN_CLIENT_SECRET_WEB_ANDA"
GOOGLE_REDIRECT_URI="http://localhost:8000/api/v1/auth/google/callback"

# Konfigurasi Database PostgreSQL
POSTGRES_SERVER="localhost"
POSTGRES_PORT="5432"
POSTGRES_USER="nama_user_db_anda"
POSTGRES_PASSWORD="password_db_anda"
POSTGRES_DB="fotota_db"
DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}:${POSTGRES_PORT}/${POSTGRES_DB}"

# Pengaturan JWT (Ganti dengan kunci rahasia Anda yang kuat dan acak)
JWT_SECRET_KEY="secret-key-untuk-access-token"
JWT_REFRESH_SECRET_KEY="secret-key-lain-untuk-refresh-token"
JWT_EVENT_SECRET_KEY="secret-key-ketiga-untuk-event-access-token"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Pengaturan model DeepFace
DEEPFACE_MODEL_NAME="Dlib"

# Pengaturan Storage Paths (Gunakan path absolut)
STORAGE_ROOT_PATH=/home/your-user/storage

# Pengaturan oneDNN (library optimasi CPU) -> 1 untuk aktif, 0 untuk nonaktif
TF_ENABLE_ONEDNN_OPTS=0
```

### 3\. Setup Virtual Environment & Dependensi

```bash
# Buat virtual environment
python -m venv venv

# Aktifkan
# Windows:
# venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install semua library yang dibutuhkan
pip install -r requirements.txt
```

### 4\. Setup Database

Jalankan skrip SQL di bawah ini pada database PostgreSQL Anda untuk membuat semua tabel yang diperlukan.

```sql
-- Hapus tabel jika sudah ada (opsional, untuk memulai dari bersih)
DROP TABLE IF EXISTS fotota, activity, images, events, users CASCADE;

-- Tabel untuk Pengguna
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    picture TEXT,
    selfie TEXT,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    google_id VARCHAR(255) NOT NULL UNIQUE,
    google_refresh_token TEXT,
    internal_refresh_token_hash VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Tabel untuk Events
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    date TIMESTAMP WITH TIME ZONE,
    hashed_password VARCHAR(255) NOT NULL,
    description TEXT,
    link VARCHAR(255) UNIQUE,
    id_user INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    indexed_by_robota BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Tabel untuk Gambar/Foto
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    id_event INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Tabel untuk log aktivitas
CREATE TABLE activity (
    id SERIAL PRIMARY KEY,
    id_event INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    id_user INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Tabel untuk foto yang di-bookmark
CREATE TABLE fotota (
    id SERIAL PRIMARY KEY,
    id_user INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    id_image INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Membuat Indeks untuk mempercepat pencarian
CREATE INDEX ix_users_id ON users(id);
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_google_id ON users(google_id);
CREATE INDEX ix_events_id ON events(id);
CREATE INDEX ix_events_name ON events(name);
CREATE INDEX ix_images_id ON images(id);
CREATE INDEX ix_activity_id ON activity(id);
CREATE INDEX ix_fotota_id ON fotota(id);
```

### Menjalankan Aplikasi

Pastikan Anda berada di direktori `backend/` dan virtual environment Anda aktif.

```bash
uvicorn app.main:app --reload
```

  - `--reload`: Server akan otomatis restart saat Anda mengubah kode.

Server akan berjalan di `http://localhost:8000`.

### Dokumentasi API

Setelah server berjalan, dokumentasi API interaktif (Swagger UI) tersedia di:
**[http://localhost:8000/api/v1/docs](https://www.google.com/search?q=http://localhost:8000/api/v1/docs)**

-----

## Konfigurasi Nginx untuk Produksi (Direkomendasikan)

Untuk lingkungan produksi, tidak disarankan menjalankan Uvicorn secara langsung. Sebaiknya gunakan Nginx sebagai *reverse proxy* dan *media server* untuk performa, keamanan, dan keandalan yang lebih baik.

### Prasyarat

  - Nginx sudah terinstal di server Anda (`sudo apt install nginx`).
  - Anda memiliki nama domain yang sudah diarahkan ke IP publik server Anda (opsional, bisa menggunakan IP).

### Langkah 1: Fondasi - Direktori dan Izin Akses

Langkah ini krusial untuk mencegah error '403 Forbidden' (gagal baca) dan error saat aplikasi mencoba membuat folder (gagal tulis).

1.  **Buat Struktur Direktori:** Gunakan path yang sama dengan variabel `STORAGE_ROOT_PATH` di file `.env` Anda.

    ```bash
    # Ganti '/home/your-user/storage' dengan path asli Anda
    sudo mkdir -p /home/your-user/storage/events
    sudo mkdir -p /home/your-user/storage/selfies
    ```

2.  **Atur Kepemilikan & Izin Akses:**

      - Aplikasi FastAPI (dijalankan oleh user Anda, misal: `zul-fadli`) perlu izin *tulis*.
      - Nginx (dijalankan oleh user `www-data`) perlu izin *baca*.

    <!-- end list -->

    ```bash
    # Ganti 'your-user' dengan username Anda yang menjalankan aplikasi
    sudo chown -R your-user:www-data /home/your-user/storage

    # Beri izin rwx untuk pemilik & grup, dan r-x untuk lainnya
    sudo chmod -R 775 /home/your-user/storage

    # (SANGAT PENTING) Izinkan Nginx melintasi direktori home Anda
    sudo chmod 755 /home/your-user
    ```

### Langkah 2: Membuat File Konfigurasi Nginx

1.  Buat file konfigurasi baru untuk proyek Anda.

    ```bash
    sudo nano /etc/nginx/sites-available/fotota
    ```

2.  Salin dan tempel konfigurasi berikut. **Perhatikan dan ganti nilai yang ditandai.**

    ```nginx
    server {
        # Ganti 'api.domainanda.com' dengan domain atau IP publik server Anda
        server_name api.domainanda.com;

        # BLOK 1: REVERSE PROXY UNTUK API FASTAPI
        # Meneruskan semua request ke aplikasi FastAPI yang berjalan di port 8000
        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # BLOK 2: MEDIA SERVER UNTUK FILE STATIS
        # Menyajikan file dari storage jika URL diawali /media/
        location /media/ {
            # PENTING: Ganti path ini agar SAMA PERSIS dengan nilai
            # STORAGE_ROOT_PATH di file .env Anda.
            alias /home/your-user/storage/;

            # Opsi tambahan
            expires 30d;
            add_header Cache-Control "public";
            autoindex off;
        }

        listen 80; # Port HTTP standar
    }
    ```

### Langkah 3: Mengaktifkan Konfigurasi & Menjalankan Aplikasi

1.  **Aktifkan Konfigurasi:** Buat symbolic link.

    ```bash
    # Hapus link default jika ada
    sudo rm /etc/nginx/sites-enabled/default

    # Buat link baru untuk konfigurasi fotota
    sudo ln -s /etc/nginx/sites-available/fotota /etc/nginx/sites-enabled/
    ```

2.  **Tes dan Reload Nginx:**

    ```bash
    sudo nginx -t
    # Jika outputnya "test is successful", lanjutkan:
    sudo systemctl reload nginx
    ```

3.  **Jalankan Aplikasi FastAPI:** Di lingkungan produksi, gunakan Gunicorn.

    ```bash
    # Pastikan virtual environment (venv) aktif
    source venv/bin/activate

    # Jalankan dengan Gunicorn
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
    ```

      - `-w 4`: Menjalankan 4 proses worker (sesuaikan dengan jumlah core CPU Anda).
      - `-k uvicorn.workers.UvicornWorker`: Menggunakan worker Uvicorn yang asinkron.

Untuk menjalankan aplikasi secara permanen di latar belakang, disarankan menggunakan process manager seperti `systemd`.

-----

## Menjalankan dengan Docker (Direkomendasikan)

Ini adalah cara terbaik untuk memastikan lingkungan pengembangan yang konsisten, portabel, dan siap untuk produksi.

### 1\. Prasyarat Docker

Docker Desktop (untuk Windows/Mac) atau Docker Engine (untuk Linux) sudah terinstal dan sedang berjalan.

Server PostgreSQL berjalan di mesin Anda (bisa di localhost atau di VM GCP).

### 2\. Konfigurasi .env untuk Docker

Sebelum membangun image, pastikan file `.env` Anda dikonfigurasi dengan benar agar kontainer bisa terhubung ke database.

  - Jika Database Anda berjalan di laptop (localhost):

    ```
    POSTGRES_SERVER=host.docker.internal
    ```

    (host.docker.internal adalah alamat khusus yang merujuk ke mesin host dari dalam kontainer Docker).

  - Jika Database Anda berjalan di VM GCP:

    ```
    POSTGRES_SERVER=<ALAMAT_IP_PUBLIK_VM_GCP_ANDA>
    ```

Pastikan untuk semua kredensial database di `.env` benar.

Pastikan juga firewall GCP dan konfigurasi PostgreSQL di VM mengizinkan koneksi eksternal.

> Note: Terkadang penggunaan tanda kutip ("") pada isi dari variable di `.env` dapat menyebabkan error saat runing time.

### 3\. Alur Kerja Build Docker (Dua Tahap)

Kita menggunakan pendekatan dua tahap untuk build yang lebih cepat dan image yang lebih kecil.

Pendekatan dua tahap ini digunakan karena library-library yang digunakan untuk `DeepFace` sangat besar.

#### Tahap A: Bangun Base Image (Fondasi)

Tahap ini berat dan lambat, berisi semua instalasi dependensi. Anda hanya perlu menjalankannya sekali saja, atau setiap kali Anda mengubah requirements.txt.

```shell
docker build -f Dockerfile.base -t fotota-backend-base:local-build .
```

  - `-f` Dockerfile.base: Secara eksplisit menggunakan file Dockerfile.base.
  - `-t` fotota-backend-base:local-build: Memberi nama "fondasi" kita.

#### Tahap B: Bangun Image Aplikasi

Tahap ini sangat cepat. Ia akan menggunakan "fondasi" yang sudah jadi dan hanya menumpuk kode aplikasi Anda di atasnya. Jalankan ini setiap kali Anda mengubah kode Python.

```shell
docker build -t fotota-backend .
```

### 4\. Menjalankan Docker Container

Setelah image fotota-backend berhasil dibuat, jalankan dengan perintah berikut:

```shell
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  -v ./storage:/app/storage \
  --name fotota-api \
  fotota-backend
```

Penjelasan Perintah:

  - `docker run`: Perintah utama untuk menjalankan sebuah container.
  - `-d`: Menjalankan container di latar belakang (detached mode).
  - `-p` 8000:8000: Memetakan port 8000 di laptop Anda ke port 8000 di dalam container.
  - `--env-file .env`: Menyuntikkan semua variabel konfigurasi dari file .env Anda ke dalam container.
  - `-v` ./storage:/app/storage: Menautkan folder storage di laptop Anda ke /app/storage di dalam container. Ini membuat data unggahan Anda permanen.
  - `--name fotota-api`: Memberi nama yang mudah diingat pada container Anda.
  - `fotota-backend`: Nama image yang akan dijalankan.

### 5\. Mengelola Container

  - Melihat container yang berjalan: `docker ps` atau `docker ps -a`
  - Melihat log aplikasi: `docker logs -f fotota-api` (`-f` untuk mengikuti log secara real-time).
  - Menghentikan container: `docker stop fotota-api`
  - Menjalankan kembali container yang sudah ada: `docker start fotota-api`
  - Menghapus container (setelah dihentikan): `docker rm fotota-api`