# app/core/model_loader.py

import insightface

class FaceAnalysisService:
    def __init__(self):
        print("Initializing FaceAnalysis service...")
        # Muat model. 'buffalo_l' adalah model serbaguna yang baik.
        # providers=['CPUExecutionProvider'] memastikan ia berjalan di CPU.
        try:
            self.app = insightface.app.FaceAnalysis(
                name="buffalo_l", 
                providers=['CPUExecutionProvider']
            )
            # Siapkan model. det_size adalah ukuran gambar input untuk deteksi.
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            print("✅ Insightface models loaded successfully.")
        except Exception as e:
            print(f"❌ CRITICAL: Failed to load Insightface models. Error: {e}", exc_info=True)
            self.app = None # Set app menjadi None jika gagal load

# Buat satu instance global yang akan digunakan di seluruh aplikasi
face_app = FaceAnalysisService()