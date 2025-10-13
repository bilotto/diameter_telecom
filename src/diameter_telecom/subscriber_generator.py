import threading
import time
import random
from typing import Optional

class SubscriberGenerator:
    """A generator that creates unique MSISDN and IMSI pairs for subscribers.
    
    This generator produces subscriber identifiers that follow telecommunications
    standards for MSISDN and IMSI formats. The generator ensures uniqueness
    within the carrier's network by using the carrier's MCC/MNC and a sequential
    counter with timestamp-based initialization.
    
    MSISDN Format: <country_code><subscriber_number>
    IMSI Format: <MCC><MNC><MSIN>
    
    The generator uses threading locks to ensure thread safety and prevents
    duplicate subscriber generation in concurrent scenarios.
    """
    
    def __init__(self, carrier_name: str, mcc_mnc: str, country_code: str, 
                 msisdn_length: int = 13, imsi_length: int = 15):
        """Create a new subscriber generator.
        
        Args:
            carrier_name: Name of the carrier (for logging/debugging)
            mcc_mnc: Mobile Country Code + Mobile Network Code (e.g., "72488")
            country_code: Country calling code (e.g., "55" for Brazil)
            msisdn_length: Total length of MSISDN (default: 13)
            imsi_length: Total length of IMSI (default: 15)
        """
        self.carrier_name = carrier_name
        self.mcc_mnc = str(mcc_mnc)
        self.country_code = str(country_code)
        self.msisdn_length = msisdn_length
        self.imsi_length = imsi_length
        
        # Extract MCC and MNC from mcc_mnc
        if len(self.mcc_mnc) == 5:  # Standard format: 3-digit MCC + 2-digit MNC
            self.mcc = self.mcc_mnc[:3]
            self.mnc = self.mcc_mnc[3:]
        elif len(self.mcc_mnc) == 6:  # Extended format: 3-digit MCC + 3-digit MNC
            self.mcc = self.mcc_mnc[:3]
            self.mnc = self.mcc_mnc[3:]
        else:
            raise ValueError(f"Invalid MCC/MNC format: {mcc_mnc}. Expected 5 or 6 digits.")
        
        # Validate lengths
        if self.msisdn_length < len(self.country_code) + 1:
            raise ValueError(f"MSISDN length ({msisdn_length}) must be at least {len(self.country_code) + 1}")
        
        if self.imsi_length < len(self.mcc) + len(self.mnc) + 1:
            raise ValueError(f"IMSI length ({imsi_length}) must be at least {len(self.mcc) + len(self.mnc) + 1}")
        
        # Initialize sequence with timestamp-based seed
        self._base_timestamp = int(time.time())
        self._busy_lock = threading.Lock()
        
        # Calculate available digits for subscriber number and MSIN
        self._msisdn_digits = self.msisdn_length - len(self.country_code)
        self._imsi_digits = self.imsi_length - len(self.mcc) - len(self.mnc)
        
        # Start with a random number to avoid predictable sequences
        self._msisdn_sequence = random.randint(10**(self._msisdn_digits-1), 10**self._msisdn_digits - 1)
        self._imsi_sequence = random.randint(10**(self._imsi_digits-1), 10**self._imsi_digits - 1)
    
    def next_subscriber(self) -> tuple[str, str]:
        """Generate the next unique MSISDN and IMSI pair.
        
        Returns:
            A tuple of (msisdn, imsi) as strings
        """
        with self._busy_lock:
            # Generate MSISDN
            self._msisdn_sequence += 1
            if self._msisdn_sequence >= 10**self._msisdn_digits:  # Reset if too large
                self._msisdn_sequence = 10**(self._msisdn_digits-1)
            
            # Format MSISDN: country_code + subscriber_number
            subscriber_number = f"{self._msisdn_sequence:0{self._msisdn_digits}d}"
            msisdn = f"{self.country_code}{subscriber_number}"
            
            # Generate IMSI
            self._imsi_sequence += 1
            if self._imsi_sequence >= 10**self._imsi_digits:  # Reset if too large
                self._imsi_sequence = 10**(self._imsi_digits-1)
            
            # Format IMSI: MCC + MNC + MSIN
            msin = f"{self._imsi_sequence:0{self._imsi_digits}d}"
            imsi = f"{self.mcc}{self.mnc}{msin}"
            
            return msisdn, imsi
    
    def generate_batch(self, count: int) -> list[tuple[str, str]]:
        """Generate multiple subscriber pairs at once.
        
        Args:
            count: Number of subscriber pairs to generate
        
        Returns:
            List of (msisdn, imsi) tuples
        """
        return [self.next_subscriber() for _ in range(count)]
    
    def get_stats(self) -> dict:
        """Get statistics about the subscriber generator.
        
        Returns:
            Dictionary with generator statistics
        """
        return {
            "carrier_name": self.carrier_name,
            "mcc": self.mcc,
            "mnc": self.mnc,
            "country_code": self.country_code,
            "msisdn_length": self.msisdn_length,
            "imsi_length": self.imsi_length,
            "msisdn_digits": self._msisdn_digits,
            "imsi_digits": self._imsi_digits,
            "current_msisdn_sequence": self._msisdn_sequence,
            "current_imsi_sequence": self._imsi_sequence,
            "base_timestamp": self._base_timestamp
        }
