from collections import OrderedDict
from rest_framework.utils.model_meta import _get_pk

from .endpoint_enumerator import EndpointEnumerator
from .inspectors import ViewSchema
from .utils import is_list_view


def common_path(paths):
    split_paths = [path.strip('/').split('/') for path in paths]
    s1 = min(split_paths)
    s2 = max(split_paths)
    common = s1
    for i, c in enumerate(s1):
        if c != s2[i]:
            common = s1[:i]
            break
    return '/' + '/'.join(common)


INSERT_INTO_COLLISION_FMT = """
Schema Naming Collision.
coreapi.Link for URL path {value_url} cannot be inserted into schema.
Position conflicts with coreapi.Link for URL path {target_url}.
Attemped to insert link with keys: {keys}.
Adjust URLs to avoid naming collision or override `SchemaGenerator.get_keys()`
to customise schema structure.
"""


def insert_into(target, keys, value):
    """
    Nested dictionary insertion.
    >>> example = {}
    >>> insert_into(example, ['a', 'b', 'c'], 123)
    >>> example
    {'a': {'b': {'c': 123}}}
    """
    for key in keys[:-1]:
        if key not in target:
            target[key] = {}
        target = target[key]
    try:
        target[keys[-1]] = value
    except TypeError:
        msg = INSERT_INTO_COLLISION_FMT.format(
            value_url=value.url,
            target_url=target.url,
            keys=keys
        )
        raise ValueError(msg)


def is_custom_action(action):
    return action not in set([
        'retrieve', 'list', 'create', 'update', 'partial_update', 'destroy'
    ])


class SchemaGenerator:
    default_mapping = {
        'get': 'retrieve',
        'post': 'create',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    }

    def __init__(self):
        self.endpoints = EndpointEnumerator().api_endpoints

        links = OrderedDict()

        # Generate (path, method, view) given (path, method, callback)
        view_endpoints = []
        paths = []
        for path, method, callback in self.endpoints:
            view = self.create_view(callback, method)
            path = self.coerce_path(path, method, view)
            paths.append(path)
            view_endpoints.append((path, method, view))

        prefix = self.find_prefix(paths)

        for path, method, view in view_endpoints:
            # TODO: Check permission

            link = ViewSchema(view, path, method)
            subpath = path[len(prefix):]
            keys = self.get_keys(subpath, method, view)
            insert_into(links, keys, link)

        self.links = links

    def create_view(self, callback, method):
        view = callback.cls()
        for attr, val in getattr(callback, 'initkwargs', {}).items():
            setattr(view, attr, val)

        view.args = ()
        view.kwargs = {}
        view.format_kwarg = None
        view.request = None

        actions = getattr(callback, 'actions', None)
        view.action_map = actions
        if actions is not None:
            if method == 'OPTIONS':
                view.action = 'metadata'
            else:
                view.action = actions.get(method.lower())

        return view

    def coerce_path(self, path, method, view):
        # TODO Handle versioning properly
        if '{version}' in path:
            path = path.replace('{version}', 'v1')

        if '{pk}' not in path:
            return path

        model = getattr(getattr(view, 'queryset', None), 'model', None)
        if model:
            field_name = _get_pk(model._meta.concrete_model._meta).name
        else:
            field_name = 'id'

        return path.replace('{pk}', '{%s}' % field_name)

    def find_prefix(self, paths):
        prefixes = []
        for path in paths:
            components = path.strip('/').split('/')
            initial_components = []
            for component in components:
                if '{' in component:
                    break
                initial_components.append(component)

            prefix = '/'.join(initial_components[:-1])
            if not prefix:
                # We can just break early in the case that there's at least
                # one URL that doesn't have a path prefix.
                return '/'
            prefixes.append('/' + prefix + '/')
        return common_path(prefixes)

    def get_keys(self, subpath, method, view):
        if hasattr(view, 'action'):
            action = view.action
        else:
            if is_list_view(subpath, method, view):
                action = 'list'
            else:
                action = self.default_mapping[method.lower()]

        named_path_components = [
            component for component
            in subpath.strip('/').split('/')
            if '{' not in component or component == '{version}'
        ]

        if is_custom_action(action):
            if len(view.action_map) > 1:
                action = self.default_mapping[method.lower()]
                return named_path_components + [action]
            else:
                return named_path_components[:-1] + [action]

        return named_path_components + [action]
