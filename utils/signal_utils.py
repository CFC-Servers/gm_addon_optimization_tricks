import signal
import threading


def register_sigint_handler(handler):
    """Register a SIGINT handler only when running on the main thread.

    Safe to call from background threads; it will no-op there. Any exceptions
    from signal registration (e.g., non-main interpreter contexts) are ignored.
    """
    try:
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, handler)
    except Exception:
        # Ignore environments where signals can't be set (e.g., some embedded runtimes)
        pass


def register_signal_handler(sig: int, handler):
    """Generic variant to register any signal safely from the main thread only."""
    try:
        if threading.current_thread() is threading.main_thread():
            signal.signal(sig, handler)
    except Exception:
        pass
