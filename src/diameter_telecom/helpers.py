from .diameter import DiameterMessage

def create_diameter_message_from_file(filename) -> DiameterMessage:
    with open(filename, "r") as f:
        file_content = f.read()
    return DiameterMessage(file_content)


from .diameter.session._diameter_session import DiameterSession
from typing import Dict
def dump_sessions(sessions: Dict[str, DiameterSession], output_file: str) -> str:
    # Dump session_ids to file
    with open(output_file, "w") as f:
        for session_id in sessions.keys():
            f.write(f"{session_id}\n")
    return output_file