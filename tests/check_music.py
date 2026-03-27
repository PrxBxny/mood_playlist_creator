from dotenv import load_dotenv
load_dotenv()

from app.config import get_config
from app.models.schemas import MoodRequest
from app.services.music_service import MusicService


cfg = get_config()
music_service = MusicService(config=cfg)
mood_request = MoodRequest(mood_tags=["phonk", "agressive"])

tracks = music_service.get_tracks(mood=mood_request, limit=6)
for track in tracks:
    print(track.model_dump())