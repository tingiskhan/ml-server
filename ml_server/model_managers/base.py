import onnxruntime as rt
from ..db.enums import SerializerBackend, ModelStatus
import dill
import platform
from datetime import datetime


# TODO: Perhaps use YAML as base to streamline?
class BaseModelManager(object):
    def __init__(self):
        """
        Defines a base class for model management.
        """

        self._logger = None

    def set_logger(self, logger):
        self._logger = logger

    def close_all_running(self):
        """
        Closes all running tasks for this node. Called when starting the app to avoid having "broken" models.
        """

        raise NotImplementedError()

    def pre_model_start(self, name, key, backend):
        """
        What to do before starting model. E.g. create a database entry or a YAML-file.
        :param name: The name of the model
        :type name: str
        :param key: The key
        :type key: str
        :param backend: The backend to use
        :type backend: SerializerBackend
        :return: Self
        :rtype: BaseModelManager
        """

        asdict = {
            'upd_by': platform.node(),
            'model_name': name,
            'hash_key': key,
            'status': ModelStatus.Running,
            'start_time': datetime.now(),
            'backend': backend
        }

        self._persist(asdict)

        return self

    def model_fail(self, name, key, backend):
        """
        What to do on model fail.
        :type name: str
        :param key: The key
        :type key: str
        :param backend: The backend to use
        :type backend: SerializerBackend
        :return: Self
        :rtype: BaseModelManager
        """

        data = self._get_data(name, key, backend, status=ModelStatus.Running)

        data['status'] = ModelStatus.Failed
        data['end_time'] = datetime.now()

        self._update(data)

        return self

    def _get_data(self, name, key, backend, status=None):
        """
        Get the data pertaining to the model.
        :param name: The name of the model
        :type name: str
        :param key: The hash key
        :type key: str
        :param backend: The backend
        :type backend: SerializerBackend
        :param status: If to filter on status
        :type status: ModelStatus
        :rtype: dict
        """

        raise NotImplementedError()

    def _persist(self, schema):
        """
        Persist the data for the first time.
        :param schema: The schema to persist.
        :type schema: dict
        :return: Self
        :rtype: BaseModelManager
        """

        raise NotImplementedError()

    def _update(self, schema):
        """
        Update an existing entry.
        :param schema: The schema to persist.
        :type schema: dict
        :return: Self
        :rtype: BaseModelManager
        """

        raise NotImplementedError()

    def check_status(self, name, key, backend):
        """
        Checks the status.
        :param name: The name of the model
        :type name: str
        :param key: The key of the model
        :type key: str
        :param backend: The backend to use
        :type backend: SerializerBackend
        :return: String indicating status
        :rtype: str
        """

        schema = self._get_data(name, key, backend)

        if schema is None:
            return None

        return schema['status']

    def load(self, name, key, backend):
        """
        Loads the model.
        :param name: The name of the model to save
        :type name: str
        :param key: The data key
        :type key: str
        :param backend: The backend to use
        :type backend: SerializerBackend
        :return: onnxruntime.InferenceSession
        """

        bytestring = self._get_data(name, key, backend, status=ModelStatus.Done)['byte_string']

        if bytestring is None:
            return None

        if backend == SerializerBackend.ONNX:
            return rt.InferenceSession(bytestring)
        elif backend == SerializerBackend.Dill:
            return dill.loads(bytestring)

    def save(self, name, key, obj, backend):
        """
        Save the model.
        :param name: The name of the model to save
        :type name: str
        :param key: The key of the data
        :type key: str
        :param obj: The model to save in byte string
        :type obj: bytes
        :param backend: The backend to use
        :type backend: SerializerBackend
        :return: None
        :rtype: None
        """

        ms = self._get_data(name, key, backend, status=ModelStatus.Running)

        ms['status'] = ModelStatus.Done
        ms['end_time'] = datetime.now()
        ms['byte_string'] = obj

        self._update(ms)

        return self

    def delete(self, name, key, backend):
        """
        Method for deleting model.
        :param name: The name of the model
        :type name: str
        :param key: The key of the model to save
        :type key: str
        :param backend: The backend to use
        :type backend: SerializerBackend
        :return: Self
        :rtype: BaseModelManager
        """

        raise NotImplementedError()
