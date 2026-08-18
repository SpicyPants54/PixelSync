from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional


@dataclass
class TransferStatus:

    filename: str

    device: str = ""

    total_bytes: int = 0

    transferred_bytes: int = 0

    percent: float = 0.0

    speed_mbps: float = 0.0

    eta_seconds: int = 0

    state: str = "pending"

    started_at: float = 0.0

    finished_at: float = 0.0

    error: str = ""



class TransferState:

    def __init__(self):

        self._lock = Lock()

        self._transfers: Dict[str, TransferStatus] = {}



    def start(
        self,
        filename,
        device="",
        total_bytes=0,
        started_at=0.0
    ):

        with self._lock:

            self._transfers[filename] = TransferStatus(
                filename=filename,
                device=device,
                total_bytes=total_bytes,
                transferred_bytes=0,
                percent=0.0,
                speed_mbps=0.0,
                eta_seconds=0,
                state="running",
                started_at=started_at
            )



    def update(

        self,

        filename,

        transferred_bytes,

        percent,

        speed_mbps,

        eta_seconds

    ):

        with self._lock:

            transfer = self._transfers.get(filename)

            if not transfer:

                return

            transfer.transferred_bytes = transferred_bytes

            transfer.percent = percent

            transfer.speed_mbps = speed_mbps

            transfer.eta_seconds = eta_seconds



    def finish(

        self,

        filename,

        finished_at=0.0

    ):

        with self._lock:

            transfer = self._transfers.get(filename)

            if not transfer:

                return

            transfer.percent = 100.0

            transfer.state = "finished"

            transfer.finished_at = finished_at



    def fail(

        self,

        filename,

        error=""

    ):

        with self._lock:

            transfer = self._transfers.get(filename)

            if not transfer:

                return

            transfer.state = "failed"

            transfer.error = error



    def get(

        self,

        filename

    ) -> Optional[TransferStatus]:

        with self._lock:

            return self._transfers.get(filename)



    def all(self):

        with self._lock:

            return list(self._transfers.values())



    def active(self):

        with self._lock:

            return [

                transfer

                for transfer in self._transfers.values()

                if transfer.state == "running"

            ]



    def clear_finished(self):

        with self._lock:

            self._transfers = {

                name: transfer

                for name, transfer in self._transfers.items()

                if transfer.state != "finished"

            }