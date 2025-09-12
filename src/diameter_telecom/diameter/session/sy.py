from ._diameter_session import *


@dataclass
class SySession(DiameterSession):
    gx_session_id: Optional[str] = field(default=None)

    def set_gx_session_id(self, gx_session_id: str):
        self.gx_session_id = gx_session_id

    def add_message(self, message):
        """Add message to session - business logic now handled by SessionManager"""
        return super().add_message(message)

    def to_json(self) -> dict:
        session_data = super().to_json()
        if self.gx_session_id:
            session_data['gx_session_id'] = self.gx_session_id
        return session_data