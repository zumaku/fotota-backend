-- Hapus tabel jika sudah ada (opsional, untuk memulai dari bersih)
DROP TABLE IF EXISTS fotota, activity, images, events, users, faces CASCADE;

-- Install Ekstensi pgvector
CREATE EXTENSION IF NOT EXISTS vector;

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

-- Tabel  untuk menyimpan setiap wajah yang terdeteksi
CREATE TABLE faces (
    id SERIAL PRIMARY KEY,
    id_image INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    embedding VECTOR(128), 
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    w INTEGER NOT NULL,
    h INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
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

CREATE INDEX ON faces USING HNSW (embedding vector_cosine_ops);

-- Catatan: Fungsi onupdate untuk updated_at akan lebih baik ditangani oleh Trigger di PostgreSQL
-- jika Anda ingin otomatisasi penuh, namun untuk saat ini model SQLAlchemy akan menanganinya saat update.