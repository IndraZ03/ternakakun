# Script Python untuk menambahkan video closing ke video utama menggunakan FFmpeg
# Pastikan FFmpeg sudah terinstal (lihat panduan sebelumnya)
# Asumsi: Video utama dari YT Short (portrait, 576x1024, 30fps, 48kHz audio)
# Video closing: 'closing.mp4' (akan di-resize dan di-pad agar match dengan utama)
# Output: 'output_with_closing.mp4'
# Proses: Menyesuaikan closing agar resolusi, framerate, dan sample rate match sebelum concat

import subprocess
import os

def add_closing(input_video, closing_video, output_video='output_with_closing.mp4'):
    """
    Fungsi untuk menambahkan video closing ke akhir video utama menggunakan FFmpeg.
    Menangani perbedaan resolusi, framerate, dan audio sample rate.
    
    Args:
    - input_video: Path ke video utama (misalnya, video YouTube yang sudah diunduh/watermark)
    - closing_video: Path ke video closing ('closing.mp4')
    - output_video: Path ke output video (default: 'output_with_closing.mp4')
    """
    if not os.path.exists(input_video):
        print(f"File video utama {input_video} tidak ditemukan!")
        return
    if not os.path.exists(closing_video):
        print(f"File closing {closing_video} tidak ditemukan!")
        return
    
    # Command FFmpeg untuk concat dua video dengan penyesuaian
    # - Target: Resolusi 576x1024, framerate 30fps, audio 48000Hz stereo
    # - Scale & pad closing: scale ke width=576, height preserve aspect, lalu pad ke 1024 height dengan black bars
    # - Set framerate closing ke 30fps
    # - Resample audio closing ke 48000Hz
    command = [
        'ffmpeg',
        '-i', input_video,
        '-i', closing_video,
        '-filter_complex',
        '[1:v]scale=576:-2,pad=576:1024:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps=30[v1]; '  # Scale, pad, set SAR, framerate
        '[1:a]aresample=48000[a1]; '  # Resample audio ke 48kHz
        '[0:v][0:a][v1][a1]concat=n=2:v=1:a=1[v][a]',  # Concat
        '-map', '[v]',
        '-map', '[a]',
        '-c:v', 'libx264',  # Encode video
        '-preset', 'medium',  # Kualitas encode
        '-crf', '23',  # Kualitas (lebih rendah = lebih baik)
        '-c:a', 'aac',  # Encode audio
        '-b:a', '128k',  # Bitrate audio
        output_video
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Video closing berhasil ditambahkan! Output: {output_video}")
    except subprocess.CalledProcessError as e:
        print(f"Error saat menambahkan closing: {e}")
    except FileNotFoundError:
        print("FFmpeg tidak ditemukan! Pastikan sudah ditambahkan ke PATH.")

# Contoh penggunaan
if __name__ == "__main__":
    input_video = input("Masukkan path ke video utama (misalnya: video.mp4): ")
    closing_video = 'closing.mp4'  # Ganti jika path berbeda
    add_closing(input_video, closing_video)