import os
from .base import BaseModelManager
import platform
from datetime import datetime
import glob
from ..enums import ModelStatus
from ..schemas import ModelSchema
import dill


class FileModelManager(BaseModelManager):
    def __init__(self, folder: str):
        """
        Defines a base class for model management.
        :param folder: The prefix for each model file
        """

        super().__init__()
        self._pref = folder
        self._ext = 'pkl'

    def initialize(self):
        if not os.path.exists(self._pref):
            os.mkdir(self._pref)

    def close_all_running(self):
        files = glob.glob(f'{self._pref}/*.{self._ext}', recursive=True)

        running = 0
        for f in files:
            with open(f, 'rb') as f_:
                schema = ModelSchema().load(dill.load(f_))

            if schema.get('upd_by') != platform.node():
                continue
            if schema['status'] != ModelStatus.Running:
                continue

            schema['end-time'] = datetime.now()
            schema['status'] = ModelStatus.Failed

            self._update(schema)

            running += 1

        if running > 0:
            self._logger.info(f'Encountered {running} running training session, but just started - closing!')

        return

    def _format_name(self, name, key, backend):
        first = f'{name}-{key}'

        return f'{first}-{backend}.{self._ext}'

    def _get_session(self, name, key, backend, status=None):
        path = f'{self._pref}/{self._format_name(name, key, backend)}'

        if not os.path.exists(path):
            return None

        with open(path, 'rb') as s:
            return ModelSchema().load(dill.load(s))

    def _persist(self, schema):
        dct = ModelSchema().dump(schema)

        path = f'{self._pref}/{self._format_name(schema["model_name"], schema["hash_key"], schema["backend"])}'
        with open(path, 'wb') as f:
            dill.dump(dct, f)

    def _update(self, schema):
        self._persist(schema)

    def delete(self, name, key, backend):
        f = glob.glob(f'{self._pref}/*{self._format_name(name, key, backend)}', recursive=True)

        if len(f) > 1:
            raise ValueError('Multiple models with same name!')

        os.remove(f[-1])

        return self
