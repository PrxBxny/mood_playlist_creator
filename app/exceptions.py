class MoodifyError(Exception):
    pass

class SporifyAuthError(MoodifyError):
    pass

class SpotifyApiError(MoodifyError):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code

class PlaylistError(MoodifyError):
    pass