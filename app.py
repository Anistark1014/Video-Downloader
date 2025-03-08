import streamlit as st
import yt_dlp
import instaloader
import os
import time
import pyperclip

# Initialize session state variables if they don't exist
if "cancel_download" not in st.session_state:
    st.session_state.cancel_download = False
if "progress" not in st.session_state:
    st.session_state.progress = 0
if "url" not in st.session_state:
    st.session_state.url = ""
if "platform" not in st.session_state:
    st.session_state.platform = "YouTube"
if "quality" not in st.session_state:
    st.session_state.quality = 2160  # Highest quality by default (4K)
if "download_folder" not in st.session_state:
    st.session_state.download_folder = os.path.expanduser("~/Downloads")
if "download_info" not in st.session_state:
    st.session_state.download_info = {}

# Download progress hook for tracking progress, size, speed, and more
def download_progress_hook(d):
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes', 1)  # Avoid division by zero
        progress = downloaded / total
        st.session_state.progress = progress

        # Download speed in KB/s
        speed = d.get('download_speed', 0) / 1024
        st.session_state.download_speed = speed

        # Downloaded size in MB
        downloaded_size = downloaded / (1024 * 1024)  # MB
        st.session_state.downloaded_size = downloaded_size

        # Total size in MB
        total_size = total / (1024 * 1024)
        st.session_state.total_size = total_size

        # Elapsed time
        elapsed_time = time.time() - d.get('start_time', time.time())
        st.session_state.elapsed_time = elapsed_time

        # Update download info (display terminal-like information)
        st.session_state.download_info = {
            "downloaded_size": downloaded_size,
            "total_size": total_size,
            "elapsed_time": elapsed_time,
            "speed": speed
        }

        # Check for cancellation
        if st.session_state.cancel_download:
            raise Exception("Download cancelled")

def download_youtube_video(url, download_folder, quality):
    ydl_opts = {
        'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
        'progress_hooks': [download_progress_hook],
        'noplaylist': True,
        'start_time': time.time(),  # Track download start time
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def download_instagram_video(url, download_folder):
    L = instaloader.Instaloader()
    shortcode = url.rstrip('/').split("/")[-1]
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    L.download_post(post, target=download_folder)

def start_download(url, platform, quality, download_folder):
    st.session_state.cancel_download = False  # Reset cancellation flag
    st.session_state.progress = 0  # Reset progress
    st.session_state.download_speed = 0
    st.session_state.downloaded_size = 0

    # Check if the URL is a valid YouTube URL or a search term
    if platform == "YouTube":
        if "youtube.com" in url or "youtu.be" in url:
            # Proceed with the URL as it is
            try:
                download_youtube_video(url, download_folder, quality)
                st.success("Download complete!")
            except Exception as e:
                st.error(f"Error during download: {e}")
        else:
            # Use ytsearch if it's not a valid YouTube URL (treat as a search term)
            search_url = f"ytsearch:{url}"  # Format the search term for yt-dlp
            try:
                download_youtube_video(search_url, download_folder, quality)
                st.success("Download complete!")
            except Exception as e:
                st.error(f"Error during download: {e}")
    elif platform == "Instagram":
        try:
            download_instagram_video(url, download_folder)
            st.success("Download complete!")
        except Exception as e:
            st.error(f"Error during download: {e}")

def quick_download():
    # This function grabs the last copied URL from the clipboard and starts the download
    url = pyperclip.paste()  # Get the latest URL from the clipboard
    if url:
        platform = "YouTube"  # Default to YouTube for quick download
        quality = 2160  # Highest quality (4K) for quick download
        download_folder = st.session_state.download_folder
        start_download(url, platform, quality, download_folder)
    else:
        st.error("No URL found in clipboard!")

# ------------------ Streamlit UI Layout ------------------

st.title("Video Downloader")

# Quick Download button (grabs URL from clipboard)
if st.button("Quick Download (from Clipboard)"):
    quick_download()

# Input for video URL
url_input = st.text_input("Video URL", key="url", value=st.session_state.url)

# Select the platform
st.selectbox("Select Platform", ["YouTube", "Instagram"], key="platform", index=["YouTube", "Instagram"].index(st.session_state.platform))

# For YouTube, let the user select video quality
if st.session_state.platform == "YouTube":
    st.selectbox("Select Quality (YouTube Only)", [360, 480, 720, 1080, 1440, 2160], key="quality", index=[360, 480, 720, 1080, 1440, 2160].index(st.session_state.quality))
else:
    st.session_state.quality = 2160  # default value if not YouTube

# Input for download folder
default_folder = os.path.expanduser("~/Downloads")
st.text_input("Download Folder", value=st.session_state.download_folder, key="download_folder")

# Start Download button
if st.button("Start Download"):
    start_download(url_input, st.session_state.platform, st.session_state.quality, st.session_state.download_folder)


# Cancellation button – clicking this sets the cancellation flag
if st.button("Cancel Download"):
    st.session_state.cancel_download = True

# Display download progress and terminal-like status information
if st.session_state.progress > 0:
    # Display progress bar
    progress_bar = st.progress(int(st.session_state.progress * 100))

    # Display download status information like in the terminal
    st.write(f"Downloaded: {st.session_state.download_info['downloaded_size']:.2f} MB / {st.session_state.download_info['total_size']:.2f} MB")
    st.write(f"Elapsed Time: {int(st.session_state.download_info['elapsed_time'])} seconds")
    st.write(f"Download Speed: {st.session_state.download_info['speed']:.2f} KB/s")

    # Monitor and update until download completes or is canceled
    while st.session_state.progress < 1 and not st.session_state.cancel_download:
        time.sleep(0.1)  # Sleep for a short while to avoid overloading the UI
        progress_bar.progress(int(st.session_state.progress * 100))
        st.write(f"Downloaded: {st.session_state.download_info['downloaded_size']:.2f} MB / {st.session_state.download_info['total_size']:.2f} MB")
        st.write(f"Elapsed Time: {int(st.session_state.download_info['elapsed_time'])} seconds")
        st.write(f"Download Speed: {st.session_state.download_info['speed']:.2f} KB/s")

    if st.session_state.progress >= 1:
        st.success("Download complete!")
