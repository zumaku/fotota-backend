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
    indexed_by_robota BOOLEAN NOT NULL DEFAULT FALSE,
    id_user INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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

-- Tabel untuk foto yang di-bookmark/disimpan oleh pengguna
CREATE TABLE fotota (
    id SERIAL PRIMARY KEY,
    id_user INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    id_image INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Tabel untuk melacak setiap sesi pencarian dari Google Drive
CREATE TABLE drive_searches (
    id SERIAL PRIMARY KEY,
    drive_folder_id VARCHAR(255) NOT NULL,
    drive_name VARCHAR(255),
    drive_url TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'processing', -- Contoh: processing, completed, failed
    id_user INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Tabel untuk menyimpan setiap gambar yang cocok yang ditemukan dari sebuah sesi pencarian
CREATE TABLE found_drive_images (
    id SERIAL PRIMARY KEY,
    id_drive_search INTEGER NOT NULL REFERENCES drive_searches(id) ON DELETE CASCADE,
    
    original_drive_id VARCHAR(255) NOT NULL, -- ID file asli di Google Drive
    file_name VARCHAR(255) NOT NULL, -- Nama file unik yang kita simpan di storage kita
    url TEXT NOT NULL UNIQUE,          -- URL publik ke file di storage kita
    
    face_coords JSONB, -- Menyimpan data x, y, w, h dalam format JSON
    similarity REAL,   -- Menyimpan skor kemiripan (0.0 - 1.0)

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Membuat Indeks untuk mempercepat pencarian
CREATE INDEX ix_users_id ON users(id);
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_google_id ON users(google_id);
CREATE INDEX ix_users_internal_refresh_token_hash ON users(internal_refresh_token_hash);

CREATE INDEX ix_events_id ON events(id);
CREATE INDEX ix_events_name ON events(name);

CREATE INDEX ix_images_id ON images(id);

CREATE INDEX ix_activity_id ON activity(id);

CREATE INDEX ix_fotota_id ON fotota(id);

-- Membuat Indeks untuk performa query yang lebih baik
CREATE INDEX ix_drive_searches_id ON drive_searches(id);
CREATE INDEX ix_drive_searches_id_user ON drive_searches(id_user);

CREATE INDEX ix_found_drive_images_id ON found_drive_images(id);
CREATE INDEX ix_found_drive_images_id_drive_search ON found_drive_images(id_drive_search);

-- Catatan: Fungsi onupdate untuk updated_at akan lebih baik ditangani oleh Trigger di PostgreSQL
-- jika Anda ingin otomatisasi penuh, namun untuk saat ini model SQLAlchemy akan menanganinya saat update.