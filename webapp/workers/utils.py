import signal


class GracefulKiller:

    exit_now = False
    signum = None

    def __init__(self):
        for sig_code in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig_code, self.handle_signal)

    def handle_signal(self, signum, frame):
        self.exit_now = True
        self.signum = signum
