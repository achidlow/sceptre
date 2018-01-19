import json
import os
from datetime import datetime

__all__ = [
    'inject_profile_caching',
]


def inject_profile_caching(session):
    if hasattr(session, '_session'):
        cred_chain = session._session.get_component('credential_provider')
        provider = cred_chain.get_provider('assume-role')
        provider.cache = JSONFileCache()
    return session


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


# copied from awscli.assumerole, with only change being to json.dumps call.
# similar fix soon to be merged to botocore hopefully:
#   https://github.com/boto/botocore/pull/1157
class JSONFileCache(object):

    CACHE_DIR = os.path.expanduser(os.path.join('~', '.aws', 'cli', 'cache'))

    def __init__(self, working_dir=CACHE_DIR):
        self._working_dir = working_dir

    def __contains__(self, cache_key):
        actual_key = self._convert_cache_key(cache_key)
        return os.path.isfile(actual_key)

    def __getitem__(self, cache_key):
        """Retrieve value from a cache key."""
        actual_key = self._convert_cache_key(cache_key)
        try:
            with open(actual_key) as f:
                return json.load(f)
        except (OSError, ValueError, IOError):
            raise KeyError(cache_key)

    def __setitem__(self, cache_key, value):
        full_key = self._convert_cache_key(cache_key)
        try:
            file_content = json.dumps(value, default=serialize_datetime)
        except (TypeError, ValueError):
            raise ValueError("Value cannot be cached, must be "
                             "JSON serializable: %s" % value)
        if not os.path.isdir(self._working_dir):
            os.makedirs(self._working_dir)
        with os.fdopen(os.open(full_key,
                               os.O_WRONLY | os.O_CREAT, 0o600), 'w') as f:
            f.truncate()
            f.write(file_content)

    def _convert_cache_key(self, cache_key):
        full_path = os.path.join(self._working_dir, cache_key + '.json')
        return full_path
