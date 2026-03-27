class MoodifyError(Exception):
    pass

class MusicServiceError(MoodifyError):
    pass

class AIServiceError(MoodifyError):
    pass

class PlaylistError(MoodifyError):
    pass