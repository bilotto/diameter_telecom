from ._diameter_session import *


@dataclass
class SySession(DiameterSession):
    gx_session_id: Optional[str] = field(default=None)

    def set_gx_session_id(self, gx_session_id: str):
        self.gx_session_id = gx_session_id

    def add_message(self, message):
        super().add_message(message)
        if message.name == SLR:
            if message.timestamp:
                self.start(message.timestamp)
            else:
                self.start()
        elif message.name == STR:
            if message.timestamp:
                self.end(message.timestamp)
            else:
                self.end()