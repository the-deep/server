# Get heirarchy level of a django model.
def get_hierarchy_level(parent_instance):
    level = 1
    while parent_instance.parent:
        level += 1
        parent_instance = parent_instance.parent
    return level
