from .diameter import DiameterMessage

def create_diameter_message_from_file(filename) -> DiameterMessage:
    with open(filename, "r") as f:
        file_content = f.read()
    return DiameterMessage(file_content)