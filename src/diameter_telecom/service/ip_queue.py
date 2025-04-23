from queue import Queue
import socket
import struct
from collections import deque
import ipaddress

def ip_to_bytes(ip):
    return socket.inet_aton(ip)

def bytes_to_ip(ip_bytes):  
    return socket.inet_ntoa(ip_bytes)

class IpQueue(Queue):
    def __init__(self, ip_range):
        """
        Initialize IpQueue.
        ip_range: Can be a CIDR notation (e.g., '10.0.0.0/21') or a tuple of start and end IPs (e.g., ('10.0.0.0', '10.0.0.100')).
        """
        super().__init__()
        if isinstance(ip_range, str) and '/' in ip_range:
            # If CIDR notation is provided
            network = ipaddress.ip_network(ip_range, strict=False)
            self.queue = self.generate_ips(str(network[0]), str(network[-1]))
        elif isinstance(ip_range, tuple) and len(ip_range) == 2:
            # If tuple of start and end IP is provided
            start_ip, end_ip = ip_range
            self.queue = self.generate_ips(start_ip, end_ip)
        else:
            raise ValueError("Invalid IP range format. Must be CIDR notation or a tuple of start and end IPs.")
        self.ip_range = ip_range

    def generate_ips(self, start_ip, end_ip):
        start = struct.unpack('>I', socket.inet_aton(start_ip))[0]
        end = struct.unpack('>I', socket.inet_aton(end_ip))[0]
        return deque([socket.inet_ntoa(struct.pack('>I', i)) for i in range(start, end+1)])

    def get_ip(self):
        return self.get()

    def put_ip(self, ip):
        self.put(ip)


class APN:
    apn: str
    ip_queue: IpQueue

    def __init__(self, apn, ip_pool_cidr):
        self.apn = apn
        self.ip_queue = IpQueue(ip_pool_cidr)

if __name__ == '__main__':
    ip_pool = IpQueue("10.0.0.0/21")
    print(ip_pool.queue)