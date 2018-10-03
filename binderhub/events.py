"""
Emit structured, discrete events when various actions happen.
"""
from traitlets.config import Configurable

import logging
from datetime import datetime
from pythonjsonlogger import jsonlogger
from traitlets import TraitType
import json
import six


class Callable(TraitType):
    """
    A trait which is callable.

    Classes are callable, as are instances
    with a __call__() method.
    """
    info_text = 'a callable'
    def validate(self, obj, value):
        if six.callable(value):
            return value
        else:
            self.error(obj, value)


class EventLog(Configurable):
    """
    Send structured events to a logging sink
    """
    handler_maker = Callable(
        config=True,
        allow_none=True,
        help="""
        Callable that returns a logging.Handler instance to send events to.

        When set to None (the default), events are discarded.
        """
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def _skip_message(record, **kwargs):
            """
            Remove 'message' from log record.

            It is always emitted with 'null', and we do not want it,
            since we are always emitting events only
            """
            del record['message']
            return json.dumps(record, **kwargs)


        self.log = logging.getLogger(__name__)
        # We don't want events to show up in the default logs
        self.log.propagate = False

        if self.handler_maker:
            self.handler = self.handler_maker(self)
            formatter = jsonlogger.JsonFormatter(json_serializer=_skip_message)
            self.handler.setFormatter(formatter)
            self.log.addHandler(self.handler)

    def _emit(self, schema, version, event):
        """
        Emit event with given schema / version in a capsule.
        """
        if not self.handler:
            # If we don't have a handler setup, ignore everything
            return
        capsule = {
            'timestamp': datetime.now().isoformat(),
            # FIXME: Validate the schema!
            'schema': schema,
            'version': version
        }
        capsule['event'] = event
        self.log.info(capsule)

    def emit_launch(self, provider, spec, status):
        """
        Helper function for emitting a launch event.

        This helps with validation too. Will eventually be
        deprecated in favor of schema validation in _emit.
        """
        self._emit('binderhub.jupyter.io/launch', 1, {
            'provider': provider,
            'spec': spec,
            'status': status
        })