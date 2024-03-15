import signal


class GracefulExit(SystemExit):
    pass


class GracefulKiller:

    exit_now = False
    signum = None

    def __init__(self, raise_ex: bool = False):
        self._raise_ex = raise_ex
        for sig_code in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig_code, self.handle_signal)

    def handle_signal(self, signum, frame):
        self.exit_now = True
        self.signum = signum
        if self._raise_ex:
            raise GracefulExit(f'{signum}')
