from project.permissions import get_project_entities


class ProjectEntityMixin:
    """
    Mixin with build in permission methods for project entities like lead,
    entry, assessments, etc.
    """
    def __getattr__(self, name):
        if not name.startswith('can_'):
            # super() does not have __getattr__ so call __getattribute__
            return super().__getattribute__(name)
        try:
            _, action = name.split('_')  # Example: can_modify
        except ValueError:
            return super().__getattribute__(name)

        selfname = self.__class__.__name__.lower()
        roleattr = '{}_{}'.format(name, selfname)  # eg: can_modify_entry

        def permission_function(user):
            role = self.project.get_role(user)
            try:
                return role is not None and getattr(role, roleattr)
            except Exception as e:
                return super().__getattribute__(name)

        return permission_function

    @classmethod
    def get_for(cls, user):
        return get_project_entities(cls, user, action='view').distinct()
