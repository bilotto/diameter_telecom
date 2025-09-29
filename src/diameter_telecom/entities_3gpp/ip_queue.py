from queue import Queue, Empty
import socket
import struct
from collections import deque
import ipaddress
from typing import Union, Tuple, Iterator
from dataclasses import dataclass, field

def ip_to_bytes(ip: str) -> bytes:
    """
    Convert an IP address string to bytes.
    
    Args:
        ip (str): IP address string (e.g., '192.168.1.1')
        
    Returns:
        bytes: IP address in bytes format
        
    Example:
        >>> ip_to_bytes('192.168.1.1')
        b'\\xc0\\xa8\\x01\\x01'
    """
    return socket.inet_aton(ip)

def bytes_to_ip(ip_bytes: bytes) -> str:
    """
    Convert IP address bytes to string.
    
    Args:
        ip_bytes (bytes): IP address in bytes format
        
    Returns:
        str: IP address string
        
    Example:
        >>> bytes_to_ip(b'\\xc0\\xa8\\x01\\x01')
        '192.168.1.1'
    """
    return socket.inet_ntoa(ip_bytes)

class IpQueue(Queue):
    """
    Queue for managing IP addresses within a specified range.
    
    This class extends the standard Queue to provide IP address management
    functionality. It can handle both CIDR notation and start/end IP ranges.
    
    Attributes:
        ip_range: Either a CIDR notation (e.g., '10.0.0.0/21') or a tuple of
                 start and end IPs (e.g., ('10.0.0.0', '10.0.0.100'))
    """
    
    def __init__(self, ip_range: Union[str, Tuple[str, str]]):
        """
        Initialize IpQueue with a range of IP addresses.
        
        Args:
            ip_range: Can be a CIDR notation (e.g., '10.0.0.0/21') or a tuple of
                     start and end IPs (e.g., ('10.0.0.0', '10.0.0.100'))
                     
        Raises:
            ValueError: If invalid IP range format is provided
        """
        super().__init__()
        self.ip_range = ip_range
        # Initialize the queue with all IPs
        for ip in self.generate_ips(ip_range):
            self.put(ip)

    def generate_ips(self, ip_range: Union[str, Tuple[str, str]]) -> Iterator[str]:
        """
        Generate IP addresses based on the provided range.
        
        Args:
            ip_range: CIDR notation or tuple of start/end IPs
            
        Returns:
            Iterator[str]: Iterator of IP addresses
            
        Raises:
            ValueError: If invalid IP range format is provided
            
        Example:
            >>> queue = IpQueue('10.0.0.0/30')
            >>> list(queue.generate_ips('10.0.0.0/30'))
            ['10.0.0.0', '10.0.0.1', '10.0.0.2', '10.0.0.3']
        """
        if isinstance(ip_range, str) and '/' in ip_range:
            # If CIDR notation is provided
            network = ipaddress.ip_network(ip_range, strict=False)
            start_ip = str(network[0])
            end_ip = str(network[-1])
        elif isinstance(ip_range, tuple) and len(ip_range) == 2:
            # If tuple of start and end IP is provided
            start_ip, end_ip = ip_range
        else:
            raise ValueError("Invalid IP range format. Must be CIDR notation or a tuple of start and end IPs.")

        start = struct.unpack('>I', socket.inet_aton(start_ip))[0]
        end = struct.unpack('>I', socket.inet_aton(end_ip))[0]
        
        for i in range(start, end + 1):
            yield socket.inet_ntoa(struct.pack('>I', i))

    def get_ip(self) -> str:
        """
        Get an IP address from the queue.
        
        Returns:
            str: An IP address
            
        Raises:
            Empty: If no IP addresses are available
            
        Example:
            >>> queue = IpQueue('10.0.0.0/30')
            >>> queue.get_ip()
            '10.0.0.0'
        """
        return self.get()

    def put_ip(self, ip: str) -> None:
        """
        Return an IP address to the queue.
        
        Args:
            ip (str): The IP address to return
            
        Example:
            >>> queue = IpQueue('10.0.0.0/30')
            >>> ip = queue.get_ip()
            >>> queue.put_ip(ip)
        """
        self.put(ip)

    @property
    def available_ips(self) -> int:
        """
        Get the number of available IP addresses.
        
        Returns:
            int: Number of available IPs
            
        Example:
            >>> queue = IpQueue('10.0.0.0/30')
            >>> queue.available_ips
            4
        """
        return self.qsize()
