class Subscriber:
    msisdn: str
    imsi: str
    def __init__(self, msisdn: str, imsi: str,):
        self.msisdn = str(msisdn)
        self.imsi = str(imsi)

    def __eq__(self, other: 'Subscriber') -> bool:
        return self.msisdn == other.msisdn and self.imsi == other.imsi

    def __hash__(self) -> int:
        return hash((self.msisdn, self.imsi))

    def __str__(self) -> str:
        return f"Subscriber(msisdn={self.msisdn}, imsi={self.imsi})"

    def __repr__(self) -> str:
        return self.__str__()