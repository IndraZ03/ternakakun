# Script Python untuk mengunduh YouTube Shorts dalam resolusi penuh (terbaik) dan menyimpan sebagai MP4
# Pastikan Anda telah menginstal library yt-dlp: pip install yt-dlp
# Dan instal ffmpeg untuk merging dan konversi ke MP4 (lihat panduan sebelumnya)

import yt_dlp

def download_yt_short(url, output_path='.'):
    """
    Fungsi untuk mengunduh video YouTube Short dalam resolusi terbaik dan menyimpan sebagai MP4.
    
    Args:
    - url: URL dari YouTube Short (contoh: https://www.youtube.com/shorts/VIDEO_ID)
    - output_path: Direktori tempat menyimpan video (default: direktori saat ini)
    """
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Unduh resolusi video dan audio terbaik
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',  # Format nama file awal
        'merge_output_format': 'mp4',  # Paksa output akhir menjadi MP4 setelah merging (memerlukan ffmpeg)
        'quiet': False,  # Tampilkan progres unduhan
        'no_warnings': True,  # Hilangkan peringatan
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            print(f"Video berhasil diunduh ke {output_path} sebagai MP4")
        except Exception as e:
            print(f"Error saat mengunduh: {e}")

# Contoh penggunaan
if __name__ == "__main__":
    short_url = input("Masukkan URL YouTube Short: ")
    download_yt_short(short_url)