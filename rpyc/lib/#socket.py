import socket


def create_socket(family=None, type=socket.SOCK_STREAM):
    """
    Creates a new socket. If family is None, it will work on both AF_INET
    and AF_INET6 (a server socket will accept both IPv4 and IPv6 connections).
    If AF_INET6 is specified explicitly, then the socket will be set to work
    with IPv6 only (the IPV6_V6ONLY socket option will be turned on).

    """
    if not family:
        _family = socket.AF_INET
        if socket.has_ipv6:
            _family = socket.AF_INET6
    sock = socket.socket(_family, type)
    if family == socket.AF_INET6:
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)
    return sock
