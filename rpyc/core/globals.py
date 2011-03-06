"""
constants used by the protocol
"""

from sys import exit as _exit

#=========================================================
# Errors
#=========================================================

class Rpyc_Exception(Exception):
    def __init__(self, err_string, err_type):
        self.args = (err_string, err_type)
        self.err_string = err_string
        self.type = err_type
    def __str__(self):
        return self.err_string
    def __repr__(self):
        return self.err_string

# Tag used by brine, proxy or pickled object
TAG_PICKLED = b"\x01"
TAG_PROXIED = b"\x02"

if len(TAG_PICKLED) != len(TAG_PROXIED):
    _exit("bad tag length")

TAG_LENGTH = len(TAG_PICKLED)

# messages
MSG_REQUEST      = 1
MSG_REPLY        = 2
MSG_EXCEPTION    = 3

# boxing
LABEL_VALUE      = 1
LABEL_TUPLE      = 2
LABEL_LOCAL_REF  = 3
LABEL_REMOTE_REF = 4

# action handlers
HANDLE_PING      = 1
HANDLE_CLOSE     = 2
HANDLE_GETROOT   = 3
HANDLE_GETATTR   = 4
HANDLE_DELATTR   = 5
HANDLE_SETATTR   = 6
HANDLE_CALL      = 7
HANDLE_CALLATTR  = 8
HANDLE_REPR      = 9
HANDLE_STR       = 10
HANDLE_CMP       = 11
HANDLE_HASH      = 12
HANDLE_DIR       = 13
HANDLE_PICKLE    = 14
HANDLE_DEL       = 15
HANDLE_INSPECT   = 16
HANDLE_BUFFITER  = 17

# optimized exceptions
EXCEPTION_STOP_ITERATION = 1
