# app/core/logging_config.py

import logging
from colorlog import ColoredFormatter

def setup_logging():
    """
    Mengatur konfigurasi logging utama untuk aplikasi.
    """
    # 1. Buat logger utama
    log = logging.getLogger()
    log.setLevel(logging.INFO)

    # Hapus handler yang mungkin sudah ada untuk menghindari duplikasi log
    if log.hasHandlers():
        log.handlers.clear()

    # 2. Buat formatter dengan warna
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s | %(asctime)s | %(name)s:%(lineno)d | %(blue)s%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    # 3. Buat handler untuk menampilkan log di terminal
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # 4. Tambahkan handler ke logger utama
    log.addHandler(handler)

    print("Logging configured successfully with colors.")