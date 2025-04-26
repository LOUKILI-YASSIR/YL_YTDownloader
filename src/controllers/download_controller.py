import yt_dlp
import os
from datetime import datetime
from threading import Thread

class DownloadController:
    def __init__(self, database):
        self.db = database
        self.video_path = os.path.join(os.getcwd(), 'video')
        self.audio_path = os.path.join(os.getcwd(), 'audio')
        os.makedirs(self.video_path, exist_ok=True)
        os.makedirs(self.audio_path, exist_ok=True)

    def check_url(self, url, progress_callback):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Process formats
                video_formats = []
                audio_formats = []
                
                for f in info['formats']:
                    if f.get('vcodec', 'none') != 'none' and f.get('height'):
                        video_formats.append({
                            'format_id': f['format_id'],
                            'ext': f['ext'],
                            'height': f['height'],
                            'vcodec': f.get('vcodec', 'unknown'),
                            'filesize': f.get('filesize', 0),
                            'tbr': f.get('tbr', 0)
                        })
                    elif f.get('acodec', 'none') != 'none' and f.get('abr'):
                        audio_formats.append({
                            'format_id': f['format_id'],
                            'ext': f['ext'],
                            'abr': f['abr'],
                            'acodec': f.get('acodec', 'unknown'),
                            'filesize': f.get('filesize', 0)
                        })
                
                # Sort formats
                video_formats.sort(key=lambda x: (x['height'], x.get('tbr', 0)), reverse=True)
                audio_formats.sort(key=lambda x: x['abr'], reverse=True)
                
                return {
                    'success': True,
                    'info': info,
                    'video_formats': video_formats,
                    'audio_formats': audio_formats
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def download(self, url, content_type, format_type, quality, download_path, username, progress_callback):
        def download_thread():
            try:
                # Get format mappings
                format_mappings = {
                    "Vidéo": {
                        "mp4": "MP4 (Recommended)",
                        "webm": "WebM",
                        "mkv": "MKV",
                        "avi": "AVI"
                    },
                    "Audio": {
                        "mp3": "MP3 (Recommended)",
                        "wav": "WAV (High Quality)",
                        "aac": "AAC",
                        "m4a": "M4A",
                        "opus": "Opus"
                    }
                }
                
                # Get the actual format from the display name
                target_format = next(k for k, v in format_mappings[content_type].items() if v == format_type)
                
                # Get quality without the bitrate info for videos
                if content_type == "Vidéo":
                    quality = quality.split(" ")[0].replace('p', '')
                else:
                    quality = quality.replace('kbps', '')
                
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': f'{quality}+bestaudio' if content_type == "Vidéo" else f'bestaudio[abr<={quality}]',
                    'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [progress_callback],
                    'postprocessors': []
                }
                
                # Add format conversion if needed
                if content_type == "Vidéo":
                    ydl_opts['postprocessors'].append({
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': target_format,
                    })
                else:
                    ydl_opts['postprocessors'].append({
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': target_format,
                        'preferredquality': quality,
                    })

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url)
                    
                    # Calculate file size in MB
                    file_path = os.path.join(download_path, f"{info.get('title', 'video')}.{target_format}")
                    filesize = round(os.path.getsize(file_path) / (1024 * 1024), 2) if os.path.exists(file_path) else 'N/A'
                    
                    # Save download history
                    self.db.save_download(
                        username=username,
                        title=info.get('title', 'video'),
                        content_type=content_type,
                        quality=quality,
                        url=url,
                        thumbnail_url=info.get('thumbnail', ''),
                        format_type=target_format,
                        filesize=filesize
                    )
                    
                    return True, "Download completed successfully"
                    
            except Exception as e:
                return False, f"Error during download: {str(e)}"
        
        Thread(target=download_thread).start() 