from ._diameter_session import *


@dataclass
class RxSession(DiameterSession):
    gx_session_id: Optional[str] = field(default=None)

    def set_gx_session_id(self, gx_session_id: str):
        self.gx_session_id = gx_session_id

    def add_message(self, message):
        diameter_message = super().add_message(message)
        if not diameter_message:
            return
        if diameter_message.name == AAR:
            if diameter_message.timestamp:
                self.start(diameter_message.timestamp)
            # else:
            #     self.start()
        elif diameter_message.name == STR:
            if diameter_message.timestamp:
                self.end(diameter_message.timestamp)
            # else:
            #     self.end()