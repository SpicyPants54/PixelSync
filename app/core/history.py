from app.core.models import Transfer


class TransferHistory:

    def __init__(self, session):

        self.session = session


    def exists(self, file_hash):

        return (
            self.session.query(Transfer)
            .filter_by(file_hash=file_hash)
            .first()
            is not None
        )


    def add(
        self,
        filename,
        file_hash,
        size
    ):

        record = Transfer(
            filename=filename,
            file_hash=file_hash,
            file_size=size,
            status="complete"
        )

        self.session.add(record)

        self.session.commit()