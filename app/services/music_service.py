from requests import post, get
from random import randint
from math import ceil

from app.config import BaseConfig
from app.models.schemas import LastfmParams, TrackResponse, MoodRequest
from app.utils.exceptions import MusicServiceError


class MusicService:
    def __init__(self, config: BaseConfig):
        self._API_KEY = config.LASTFM_API_KEY
        self._BASE_URL = config.LASTFM_API_BASE_URL

    def get_tracks(self, mood: MoodRequest, limit:int) -> list[TrackResponse]:
        all_tracks = []

        for tag in mood.mood_tags:
            try:
                params = LastfmParams(
                    tag=tag,
                    page=randint(1, 50),
                    limit=ceil(limit / len(mood.mood_tags)),
                )
                tracks = self._fetch_by_tag(params)

                all_tracks.extend(tracks)

            except MusicServiceError:
                print(f"Не получилось обработать тег: {tag}, идем дальше")
                continue

        return all_tracks[:limit]

    def _fetch_by_tag(self, params: LastfmParams) -> list[TrackResponse]:
        query = params.model_dump()
        query["api_key"] = self._API_KEY

        try:
            response = get(self._BASE_URL, params=query, timeout=10)
        except Exception as e:
            raise MusicServiceError(f"Не удалось подключиться к Last.fm:{e}") from e

        if response.status_code != 200:
            raise MusicServiceError(f"Last.fm вернул {response.status_code}")

        data = response.json()
        tracks_dict = data["tracks"]["track"]

        # Защита от странного поведения Last.fm (один трек → dict вместо list)
        if isinstance(tracks_dict, dict):
            tracks_dict = [tracks_dict]

        return[self._track_to_model(track) for track in tracks_dict]

    def _track_to_model(self, track_dict: dict) -> TrackResponse:
        return TrackResponse(
            name=track_dict["name"],
            artist=track_dict["artist"]["name"],
            duration=track_dict["duration"],
            lastfm_url=track_dict["url"]
        )