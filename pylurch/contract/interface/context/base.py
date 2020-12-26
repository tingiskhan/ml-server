from typing import Union, List
from pyalfred.contract.interface import DatabaseInterface
from ...database import TrainingSession, Artifact, SessionException


# TODO: Move context?
class ClientContext(object):
    def __init__(self, client: DatabaseInterface, training_session: TrainingSession):
        self._client = client
        self._session = training_session

    @property
    def session(self):
        return self._session

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            try:
                self._client.create(
                    SessionException(session_id=self._session.id, type_=exc_type.__name__, message=str(exc_val))
                )
            finally:
                raise Exception("Something went wrong during the session, see full error.") from exc_val

        self.on_exit()

        return False

    def on_exit(self):
        raise NotImplementedError()


class LoadableClientContext(ClientContext):
    def get_result(self) -> Union[Artifact, List[Artifact]]:
        return self._client.get(Artifact, lambda u: u.session_id == self._session.id)
