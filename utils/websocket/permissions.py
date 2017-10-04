def lead_permissions(user, event, request):
    # For testing, currently just allow on_new event
    # for all users.
    if event == 'onNew':
        return True
    return False


permissions = {
    'leads': lead_permissions,
}
