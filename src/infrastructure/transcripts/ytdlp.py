import logging

import requests
import yt_dlp


class YtDlpTranscriptProvider:
    def __init__(self, *, logger: logging.Logger) -> None:
        self._logger = logger

    def fetch_transcript(self, video_id: str) -> str:
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        self._logger.info("Fetching transcript for %s using yt-dlp...", video_id)

        ydl_opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

        subtitle_formats = self._find_english_subtitles(info)
        subtitle_url = self._select_subtitle_url(subtitle_formats)
        self._logger.info("Found subtitle URL for %s.", video_id)

        response = requests.get(subtitle_url, timeout=30)
        response.raise_for_status()

        try:
            transcript = self._parse_json3(response.json())
            self._logger.info("Successfully fetched transcript (%s chars).", len(transcript))
            return transcript
        except Exception:
            self._logger.warning("Could not parse subtitle response as JSON3; returning raw text.")
            return response.text

    @staticmethod
    def _find_english_subtitles(info: dict) -> list[dict]:
        subtitles = info.get("subtitles", {}).get("en")
        if not subtitles:
            subtitles = info.get("automatic_captions", {}).get("en")

        if not subtitles:
            raise ValueError("No English subtitles found for this video.")

        return subtitles

    @staticmethod
    def _select_subtitle_url(subtitle_formats: list[dict]) -> str:
        for subtitle_format in subtitle_formats:
            if subtitle_format.get("ext") == "json3":
                return subtitle_format["url"]

        return subtitle_formats[0]["url"]

    @staticmethod
    def _parse_json3(payload: dict) -> str:
        transcript_parts: list[str] = []

        for event in payload.get("events", []):
            for segment in event.get("segs", []):
                text = segment.get("utf8")
                if text and text != "\n":
                    transcript_parts.append(text)

        return "".join(transcript_parts)

