from app.services.ai_service import AIService
from app.services.music_service import MusicService
from app.models.schemas import PlaylistResponse, TrackResponse


class PlaylistService:
    def __init__(self, ai_service: AIService, music_service: MusicService):
        self._ai = ai_service
        self._music = music_service

    def generate(self, user_prompt: str, number_of_tracks: int) -> PlaylistResponse:
        mood = self._ai.prompt_to_mood_tags(user_prompt)
        playlist = self._music.get_tracks(mood, number_of_tracks)
        playlist_duration = self._get_playlist_duration(playlist)
        return PlaylistResponse(tracks=playlist, duration=playlist_duration)

    def _get_playlist_duration(self, playlist: list[TrackResponse]) -> int:
        playlist_duration = 0
        for track in playlist:
            playlist_duration += track.duration

        return playlist_duration