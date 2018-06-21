from rest_framework.mixins import RetrieveModelMixin


def mark_as_list():
    def decorator(func):
        func.list_view = True
        return func
    return decorator


def mark_as_delete():
    def decorator(func):
        func.delete_view = True
        return func
    return decorator


def is_custom_action(action):
    return action not in set([
        'retrieve', 'list', 'create', 'update', 'partial_update', 'destroy'
    ])


def is_list_view(path, method, view):
    """
    Return True if the given path/method appears to represent a list view.
    """

    if hasattr(view, 'action'):
        # Viewsets have an explicitly defined action, which we can inspect.
        # If a custom action, check if the detail attribute is set
        # otherwise check if the action is `list`.
        if is_custom_action(view.action):
            action = getattr(view, view.action)
            return getattr(action, 'list_view', False) or \
                not action.detail
        return view.action == 'list'

    if method.lower() != 'get':
        return False

    if isinstance(view, RetrieveModelMixin):
        return False

    path_components = path.strip('/').split('/')
    if path_components and '{' in path_components[-1]:
        return False

    return True
