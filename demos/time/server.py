from time_service import TimeService

from rpyc.utils.server import ThreadedServer


if __name__ == "__main__":
    s = ThreadedServer(TimeService)
    s.start()
