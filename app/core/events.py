from collections import defaultdict

from loguru import logger


class TransferEvents:

    def __init__(self):

        self._listeners = defaultdict(list)

        logger.info(
            "TransferEvents initialized"
        )


    def subscribe(self, event_name, callback):

        self._listeners[event_name].append(callback)

        logger.info(
            f"Subscribed '{callback.__name__}' "
            f"to '{event_name}' "
            f"({len(self._listeners[event_name])} listeners)"
        )


    def unsubscribe(self, event_name, callback):

        if callback in self._listeners[event_name]:

            self._listeners[event_name].remove(callback)

            logger.info(
                f"Unsubscribed '{callback.__name__}' "
                f"from '{event_name}'"
            )


    def emit(self, event_name, **data):

        listeners = list(
            self._listeners.get(event_name, [])
        )

        logger.info(
            f"Emitting '{event_name}' "
            f"to {len(listeners)} listener(s)"
        )

        logger.debug(
            f"Event data: {data}"
        )

        for callback in listeners:

            try:

                logger.info(
                    f"Calling {callback.__name__}"
                )

                callback(**data)

            except Exception as error:

                logger.exception(
                    f"Transfer event '{event_name}' failed: {error}"
                )


    #
    # Convenience methods
    #

    def started(self, **data):

        logger.info(
            "TransferEvents.started() called"
        )

        self.emit(
            "started",
            **data
        )


    def progress(self, **data):

        logger.info(
            "TransferEvents.progress() called"
        )

        self.emit(
            "progress",
            **data
        )


    def finished(self, **data):

        logger.info(
            "TransferEvents.finished() called"
        )

        self.emit(
            "finished",
            **data
        )


    def failed(self, **data):

        logger.info(
            "TransferEvents.failed() called"
        )

        self.emit(
            "failed",
            **data
        )