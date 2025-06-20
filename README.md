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
  - **Pencarian Wajah Lintas Sumber**:
      - Event Internal: Admin dapat membuat event, mengunggah foto, dan melindunginya dengan password.
      - Integrasi Google Drive: Pengguna dapat memulai pencarian pada folder Google Drive publik hanya dengan memberikan link.
  - **Arsitektur AI yang Efisien**:
      - Migrasi dari Deepface ke Insightface untuk kontrol penuh dan penggunaan memori yang lebih rendah.
      - Menggunakan PostgreSQL dengan ekstensi pgvector untuk vector similarity search yang sangat cepat.
      - Proses ekstraksi wajah (embedding) berjalan sebagai background task per gambar, menjaga server tetap responsif.
  - **Siap untuk Deployment**: Dilengkapi dengan Dockerfile multi-stage yang efisien dan sistem logging profesional.

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
  - Google Cloud Platform (GCP) Project untuk kredensial OAuth dan Google Drive API

## Instalasi & Konfigurasi

Ikuti langkah-langkah ini secara berurutan untuk menjalankan proyek.

### 1\. Kloning Repositori

```bash
git clone https://github.com/zumaku/fotota-backend
cd backend
```

### 2\. Konfigurasi Environment

Buat file `.env` di dalam direktori `backend/` dengan menyalin dari `.env.example` atau dari template di bawah ini. Isi semua nilainya sesuai dengan konfigurasi Anda.

**Template `.env`:** [📄 Klik di sini](.env.example)


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

**SQL File:** [📄 Klik di sini](app/db/roleback.sql)

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