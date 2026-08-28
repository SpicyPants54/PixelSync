from collections import deque
from copy import deepcopy
from threading import RLock
from time import time

from loguru import logger


class TransferState:

    def __init__(self):

        self._lock = RLock()

        self._listeners = []

        self._recent_transfers = deque(
            maxlen=20
        )

        self._state = {
            #
            # Application
            #

            "status": "starting",


            #
            # Device
            #

            "device_connected": False,
            "device_serial": "",
            "device_model": "",
            "device_transport": "",


            #
            # Current transfer
            #

            "transfer_status": "idle",

            "current_file": "",

            "total_bytes": 0,

            "transferred_bytes": 0,

            "percent": 0,

            "speed_mbps": 0.0,

            "eta_seconds": 0.0,

            "error": "",


            #
            # Counters
            #

            "queue_count": 0,

            "completed_count": 0,

            "failed_count": 0,


            #
            # Timing
            #

            "started_at": None,

            "completed_at": None,
        }

        logger.info(
            "TransferState initialized"
        )


    #
    # Listener system
    #

    def subscribe(self, callback):

        with self._lock:

            if callback not in self._listeners:

                self._listeners.append(
                    callback
                )

        logger.debug(
            f"TransferState listener subscribed: "
            f"{callback.__name__}"
        )


    def unsubscribe(self, callback):

        with self._lock:

            if callback in self._listeners:

                self._listeners.remove(
                    callback
                )

        logger.debug(
            f"TransferState listener unsubscribed: "
            f"{callback.__name__}"
        )


    def _notify(self):

        snapshot = self.get_snapshot()

        listeners = []

        with self._lock:

            listeners = list(
                self._listeners
            )

        for callback in listeners:

            try:

                callback(
                    snapshot
                )

            except Exception as error:

                logger.exception(
                    f"TransferState listener failed: {error}"
                )


    #
    # Snapshot
    #

    def get_snapshot(self):

        with self._lock:

            snapshot = deepcopy(
                self._state
            )

            snapshot[
                "recent_transfers"
            ] = list(
                self._recent_transfers
            )

            return snapshot


    #
    # Application state
    #

    def set_app_status(
        self,
        status
    ):

        with self._lock:

            self._state[
                "status"
            ] = status

        logger.debug(
            f"Application state: {status}"
        )

        self._notify()


    #
    # Device state
    #

    def set_device(
        self,
        connected,
        serial="",
        model="",
        transport=""
    ):

        with self._lock:

            self._state[
                "device_connected"
            ] = connected

            if serial:

                self._state[
                    "device_serial"
                ] = serial

            if model:

                self._state[
                    "device_model"
                ] = model

            if transport:

                self._state[
                    "device_transport"
                ] = transport


        logger.info(
            "Device state updated: "
            f"connected={connected}, "
            f"serial={serial}, "
            f"model={model}, "
            f"transport={transport}"
        )

        self._notify()


    def device_connected(
        self,
        serial="",
        model="",
        transport=""
    ):

        self.set_device(
            connected=True,
            serial=serial,
            model=model,
            transport=transport
        )


    def device_disconnected(self):

        with self._lock:

            self._state[
                "device_connected"
            ] = False

            self._state[
                "device_transport"
            ] = ""

        logger.warning(
            "Device disconnected"
        )

        self._notify()


    #
    # Queue state
    #

    def set_queue_count(
        self,
        count
    ):

        with self._lock:

            self._state[
                "queue_count"
            ] = max(
                0,
                int(count)
            )

        self._notify()


    #
    # Transfer lifecycle
    #

    def start(
        self,
        filename,
        device="",
        total_bytes=0
    ):

        with self._lock:

            self._state[
                "transfer_status"
            ] = "transferring"

            self._state[
                "current_file"
            ] = filename

            self._state[
                "total_bytes"
            ] = int(
                total_bytes or 0
            )

            self._state[
                "transferred_bytes"
            ] = 0

            self._state[
                "percent"
            ] = 0

            self._state[
                "speed_mbps"
            ] = 0.0

            self._state[
                "eta_seconds"
            ] = 0.0

            self._state[
                "error"
            ] = ""

            self._state[
                "started_at"
            ] = time()

            self._state[
                "completed_at"
            ] = None

            if device:

                self._state[
                    "device_serial"
                ] = device


        logger.info(
            f"TransferState started: {filename}"
        )

        self._notify()


    def update(
        self,
        filename,
        transferred_bytes=0,
        percent=0,
        speed_mbps=0,
        eta_seconds=0
    ):

        with self._lock:

            #
            # Ignore stale updates from
            # another transfer.
            #

            if (
                self._state[
                    "current_file"
                ]
                and
                filename
                !=
                self._state[
                    "current_file"
                ]
            ):

                logger.debug(
                    f"Ignoring stale progress for: "
                    f"{filename}"
                )

                return


            transferred_bytes = int(
                transferred_bytes or 0
            )

            total_bytes = int(
                self._state[
                    "total_bytes"
                ] or 0
            )


            #
            # Calculate progress if
            # a valid total is available.
            #

            if total_bytes > 0:

                calculated_percent = int(
                    (
                        transferred_bytes
                        /
                        total_bytes
                    )
                    * 100
                )

            else:

                calculated_percent = int(
                    percent or 0
                )


            #
            # Do not display 100% while
            # the transfer is still active.
            #

            calculated_percent = min(
                calculated_percent,
                99
            )


            self._state[
                "transferred_bytes"
            ] = transferred_bytes

            self._state[
                "percent"
            ] = max(
                0,
                calculated_percent
            )

            self._state[
                "speed_mbps"
            ] = float(
                speed_mbps or 0
            )

            self._state[
                "eta_seconds"
            ] = float(
                eta_seconds or 0
            )


        self._notify()


    def finish(
        self,
        filename
    ):

        with self._lock:

            if (
                self._state[
                    "current_file"
                ]
                and
                filename
                !=
                self._state[
                    "current_file"
                ]
            ):

                logger.debug(
                    f"Ignoring finish event for: "
                    f"{filename}"
                )

                return


            total_bytes = self._state[
                "total_bytes"
            ]

            started_at = self._state[
                "started_at"
            ]

            completed_at = time()

            duration_seconds = 0.0


            if started_at:

                duration_seconds = max(
                    0.0,
                    completed_at - started_at
                )


            self._state[
                "transfer_status"
            ] = "completed"

            self._state[
                "transferred_bytes"
            ] = total_bytes

            self._state[
                "percent"
            ] = 100

            self._state[
                "eta_seconds"
            ] = 0.0

            self._state[
                "completed_at"
            ] = completed_at

            self._state[
                "completed_count"
            ] += 1


            self._recent_transfers.appendleft(
                {
                    "filename": filename,
                    "status": "completed",
                    "total_bytes": total_bytes,
                    "duration_seconds": duration_seconds,
                    "speed_mbps": self._state[
                        "speed_mbps"
                    ],
                    "completed_at": completed_at,
                }
            )


        logger.info(
            f"TransferState finished: {filename}"
        )

        self._notify()


    def fail(
        self,
        filename,
        error=""
    ):

        with self._lock:

            if (
                self._state[
                    "current_file"
                ]
                and
                filename
                !=
                self._state[
                    "current_file"
                ]
            ):

                logger.debug(
                    f"Ignoring failure event for: "
                    f"{filename}"
                )

                return


            self._state[
                "transfer_status"
            ] = "failed"

            self._state[
                "error"
            ] = error

            self._state[
                "eta_seconds"
            ] = 0.0

            self._state[
                "failed_count"
            ] += 1


            self._recent_transfers.appendleft(
                {
                    "filename": filename,
                    "status": "failed",
                    "total_bytes": self._state[
                        "total_bytes"
                    ],
                    "duration_seconds": 0.0,
                    "speed_mbps": 0.0,
                    "completed_at": time(),
                    "error": error,
                }
            )


        logger.error(
            f"TransferState failed: "
            f"{filename} - {error}"
        )

        self._notify()


    #
    # Reset current transfer
    #

    def clear_current_transfer(self):

        with self._lock:

            self._state.update(
                {
                    "transfer_status": "idle",

                    "current_file": "",

                    "total_bytes": 0,

                    "transferred_bytes": 0,

                    "percent": 0,

                    "speed_mbps": 0.0,

                    "eta_seconds": 0.0,

                    "error": "",

                    "started_at": None,

                    "completed_at": None,
                }
            )

        logger.debug(
            "Current transfer cleared"
        )

        self._notify()