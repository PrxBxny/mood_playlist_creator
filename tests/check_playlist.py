from dotenv import load_dotenv
load_dotenv()

from app.services.playlist_service import PlaylistService
from app.services.ai_service import AIService
from app.services.music_service import MusicService
from app.config import get_config

ai_service = AIService(get_config())
music_service = MusicService(get_config())

playlist_service = PlaylistService(ai_service, music_service)

playlist = playlist_service.generate("хочу послушать русские песни в думер стиле", number_of_tracks=40)
# print(playlist)

for track in playlist.tracks:
    print(f"трек: {track.name}, артист: {track.artist}")
print(f"продолжительность плейлиста: {playlist.duration}")