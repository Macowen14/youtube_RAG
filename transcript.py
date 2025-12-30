import yt_dlp
import requests
from logger import setup_logger

logger = setup_logger("transcript_service", "logs/app.log")

def get_youtube_transcript(video_id: str) -> str:
    """
    Fetches transcript using yt-dlp (more robust against bot detection).
    """
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    logger.info(f"Fetching transcript for {video_id} using yt-dlp...")

    # Configure yt-dlp to only get metadata and subtitles, no video download
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,      # Get auto-generated captions if manual aren't available
        'subtitleslangs': ['en'],       # Prioritize English
        'quiet': True,                  # Suppress terminal output
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            
            # 1. Check for manual subtitles first
            subtitles = info.get('subtitles', {})
            manual_subs = subtitles.get('en')
            
            # 2. Check for automatic captions if no manual subs
            if not manual_subs:
                subtitles = info.get('automatic_captions', {})
                manual_subs = subtitles.get('en')
            
            if not manual_subs:
                raise ValueError("No English subtitles found for this video.")

            # 3. Get the JSON3 format URL (easiest to parse)
            # Look for the 'json3' format, or fallback to 'vtt'
            subs_url = None
            for fmt in manual_subs:
                if fmt['ext'] == 'json3':
                    subs_url = fmt['url']
                    break
            
            # If no json3, try vtt (you would need a vtt parser, but json3 is standard for youtube)
            if not subs_url and manual_subs:
                subs_url = manual_subs[0]['url'] 

            logger.info(f"Found subtitle URL: {subs_url[:50]}...")
            
            # 4. Fetch the actual transcript data
            response = requests.get(subs_url)
            response.raise_for_status()
            
            # 5. Parse JSON3 to plain text
            # Youtube JSON3 format: {'events': [{'segs': [{'utf8': 'text...'}], ...}]}
            try:
                json_data = response.json()
                transcript_parts = []
                for event in json_data.get('events', []):
                    # Some events are just metadata/formatting
                    if 'segs' in event:
                        for seg in event['segs']:
                            if 'utf8' in seg and seg['utf8'] != '\n':
                                transcript_parts.append(seg['utf8'])
                
                full_text = "".join(transcript_parts)
                logger.info(f"Successfully fetched transcript ({len(full_text)} chars).")
                return full_text
                
            except Exception as parse_error:
                # Fallback: if it wasn't JSON3 (maybe VTT), just return raw text or clean it
                logger.warning("Could not parse as JSON3, returning raw text.")
                return response.text

    except Exception as e:
        logger.error(f"yt-dlp failed for {video_id}: {e}")
        raise e