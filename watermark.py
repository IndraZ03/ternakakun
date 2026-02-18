# Script Python untuk menambahkan watermark ke video menggunakan FFmpeg
# Pastikan FFmpeg sudah terinstal (lihat panduan sebelumnya)
# Asumsi: Video input bernama 'input.mp4' (ganti dengan nama video YouTube yang diunduh)
# Logo watermark: 'logo.png' (pastikan file ada di direktori yang sama)
# Output: 'output.mp4'
# Posisi: Di atas kiri (top-left)
# Ukuran watermark: Otomatis di-scale menjadi 20% dari lebar video (agak besar, sesuai permintaan; sesuaikan jika perlu)

import subprocess
import os

def add_watermark(input_video, logo_path, output_video='output.mp4', scale_factor=0.2):
    """
    Fungsi untuk menambahkan watermark ke video menggunakan FFmpeg.
    
    Args:
    - input_video: Path ke video input (misalnya, video YouTube yang diunduh)
    - logo_path: Path ke file logo.png
    - output_video: Path ke output video (default: 'output.mp4')
    - scale_factor: Faktor skala ukuran logo relatif terhadap lebar video (default: 0.2 untuk agak besar)
    """
    if not os.path.exists(input_video):
        print(f"File video {input_video} tidak ditemukan!")
        return
    if not os.path.exists(logo_path):
        print(f"File logo {logo_path} tidak ditemukan!")
        return
    
    # Command FFmpeg untuk tambah overlay
    # - Scale logo: iw*scale_factor (lebar logo = lebar video * factor)
    # - Posisi: x=10 (10px dari kiri), y=10 (10px dari atas)
    command = [
        'ffmpeg',
        '-i', input_video,
        '-i', logo_path,
        '-filter_complex', f'[1:v]scale=iw*{scale_factor}:-1 [logo]; [0:v][logo]overlay=10:10',
        '-c:a', 'copy',  # Copy audio tanpa re-encode
        output_video
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Watermark berhasil ditambahkan! Output: {output_video}")
    except subprocess.CalledProcessError as e:
        print(f"Error saat menambahkan watermark: {e}")
    except FileNotFoundError:
        print("FFmpeg tidak ditemukan! Pastikan sudah ditambahkan ke PATH.")

# Contoh penggunaan
if __name__ == "__main__":
    input_video = input("Masukkan path ke video input (misalnya: video.mp4): ")
    logo_path = 'logo.png'  # Ganti jika path berbeda
    add_watermark(input_video, logo_path)