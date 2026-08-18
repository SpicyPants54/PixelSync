from collections import defaultdict

from loguru import logger


class TransferEvents:

    def __init__(self):

        self._listeners = defaultdict(list)


    def subscribe(self, event_name, callback):

        self._listeners[event_name].append(callback)


    def unsubscribe(self, event_name, callback):

        if callback in self._listeners[event_name]:

            self._listeners[event_name].remove(callback)


    def emit(self, event_name, **data):

        listeners = list(
            self._listeners.get(event_name, [])
        )


        for callback in listeners:

            try:

                callback(**data)

            except Exception as error:

                logger.exception(
                    f"Transfer event '{event_name}' failed: {error}"
                )


    #
    # Convenience methods
    #

    def started(self, **data):

        self.emit(
            "started",
            **data
        )


    def progress(self, **data):

        self.emit(
            "progress",
            **data
        )


    def finished(self, **data):

        self.emit(
            "finished",
            **data
        )


    def failed(self, **data):

        self.emit(
            "failed",
            **data
        )