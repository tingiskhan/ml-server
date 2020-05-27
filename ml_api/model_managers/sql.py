from .base import BaseModelManager
import platform
from ..database import TrainingSession, Model, Base, MetaData
from datetime import datetime
from ..enums import ModelStatus


class SQLModelManager(BaseModelManager):
    def __init__(self, session):
        """
        TrainingSession manager for SQL based storing.
        :param session: The session to use
        :type session: sqlalchemy.orm.Session
        """

        super().__init__()
        self._session = session

    def initialize(self):
        Base.metadata.create_all(self._session.bind)

    def close_all_running(self):
        sessions = self._session.query(TrainingSession).filter(
            TrainingSession.status == ModelStatus.Running,
            TrainingSession.upd_by == platform.node()
        ).all()

        if not sessions:
            return

        self._logger.info(f'Encountered {len(sessions)} running training session, but just started - closing!')

        for s in sessions:
            s.end_time = datetime.now()
            s.status = ModelStatus.Failed

        self._session.commit()

        return

    def _persist(self, schema):
        model = self._session.query(Model).filter(Model.name == schema['model_name']).one_or_none()
        if not model:
            model = Model(name=schema['model_name'])
            self._session.add(model)

            model.training_sessions = []

        model.training_sessions += [
            TrainingSession(
                upd_by=schema['upd_by'],
                hash_key=schema['hash_key'],
                start_time=datetime.now(),
                status=schema['status'],
                backend=schema['backend']
            )
        ]

        self._session.commit()

        return self

    def _update(self, schema):
        session = self._session.query(TrainingSession).filter(
            TrainingSession.hash_key == schema['hash_key'],
            TrainingSession.status == ModelStatus.Running,
            TrainingSession.backend == schema['backend'],
            Model.name == schema['model_name'],
            TrainingSession.model_id == Model.id,
        ).one()  # type: TrainingSession

        session.end_time = schema['end_time']
        session.status = schema['status']
        session.byte_string = schema['byte_string']

        if 'meta_data' in schema and len(schema['meta_data']) > 0:
            session.meta_data = [
                MetaData(key=k, value=v) for k, v in schema['meta_data'].items()
            ]

        self._session.commit()

        return self

    def _get_session(self, name, key, backend, status=None):
        query = self._session.query(TrainingSession).filter(
            TrainingSession.hash_key == key,
            TrainingSession.backend == backend,
            Model.name == name,
            TrainingSession.model_id == Model.id,
        )

        if isinstance(status, ModelStatus):
            query = query.filter(TrainingSession.status == status)
        elif status is None:
            ...
        else:
            query = query.filter(TrainingSession.status.in_(status))

        model = query.order_by(TrainingSession.start_time.desc()).first()  # type: TrainingSession

        if model is None:
            return None

        return model.to_schema()

    def delete(self, name, key, backend):
        deleted = self._session.query(TrainingSession).filter(
            Model.name == name,
            TrainingSession.model_id == Model.id,
            TrainingSession.hash_key == key,
            TrainingSession.backend == backend
        ).delete(synchronize_session='fetch')

        self._session.commit()

        return self
