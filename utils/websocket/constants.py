
"""
List of all valid websocket actions
"""
websocket_actions = [
    'subscribe',
    'unsubscribe',
    'hb',
]


"""
List of all valid subscription channels.

For each channel, the user provides an event name and
a set of other required fields to further identify that
event.
"""
subcription_channels = {
    'leads': {
        'onNew': ['projectId'],
        'onEdited': ['leadId'],
        'onPreviewExtracted': ['leadId'],
    },
}
