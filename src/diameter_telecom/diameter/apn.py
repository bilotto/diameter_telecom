from queue import Queue, Empty
import socket
import struct
from collections import deque
import ipaddress
from typing import Union, Tuple, Iterator
from dataclasses import dataclass, field

def ip_to_bytes(ip: str) -> bytes:
    return socket.inet_aton(ip)

def bytes_to_ip(ip_bytes: bytes) -> str:  
    return socket.inet_ntoa(ip_bytes)

class IpQueue(Queue):
    def __init__(self, ip_range: Union[str, Tuple[str, str]]):
        """
        Initialize IpQueue.
        Args:
            ip_range: Can be a CIDR notation (e.g., '10.0.0.0/21') or a tuple of start and end IPs (e.g., ('10.0.0.0', '10.0.0.100')).
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
            Iterator of IP addresses
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
        """
        return self.get()

    def put_ip(self, ip: str) -> None:
        """
        Return an IP address to the queue.
        Args:
            ip: The IP address to return
        """
        self.put(ip)

    @property
    def available_ips(self) -> int:
        """
        Get the number of available IP addresses.
        Returns:
            int: Number of available IPs
        """
        return self.qsize()

@dataclass
class APN:
    """
    Access Point Name (APN) with IP pool management capabilities.
    """
    apn: str
    ip_pool_cidr: str
    ip_queue: IpQueue = field(init=False)
    _allocated_ips: set[str] = field(default_factory=set, init=False)

    def __post_init__(self):
        """Initialize the IP queue after the dataclass is created."""
        self.ip_queue = IpQueue(self.ip_pool_cidr)

    def allocate_ip(self) -> str:
        """
        Allocate an IP address from the pool.
        Returns:
            str: The allocated IP address
        Raises:
            Empty: If no IP addresses are available
        """
        try:
            ip = self.ip_queue.get_ip()
            self._allocated_ips.add(ip)
            return ip
        except Empty:
            raise Empty("No IP addresses available in the pool")

    def release_ip(self, ip: str) -> None:
        """
        Release an IP address back to the pool.
        Args:
            ip: The IP address to release
        """
        if ip in self._allocated_ips:
            self._allocated_ips.remove(ip)
            self.ip_queue.put_ip(ip)

    @property
    def allocated_ips(self) -> set[str]:
        """
        Get the set of currently allocated IP addresses.
        Returns:
            set[str]: Set of allocated IP addresses
        """
        return self._allocated_ips.copy()

    @property
    def available_ips(self) -> int:
        """
        Get the number of available IP addresses.
        Returns:
            int: Number of available IPs
        """
        return self.ip_queue.available_ips

if __name__ == '__main__':
    # Example usage
    apn = APN("test.apn", "10.0.0.0/21")
    print(f"Available IPs: {apn.available_ips}")
    
    # Allocate an IP
    ip = apn.allocate_ip()
    print(f"Allocated IP: {ip}")
    print(f"Allocated IPs: {apn.allocated_ips}")
    
    # Release the IP
    apn.release_ip(ip)
    print(f"Available IPs after release: {apn.available_ips}")