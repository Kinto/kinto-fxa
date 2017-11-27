from pyramid.exceptions import ConfigurationError
from collections import OrderedDict


def fxa_conf(request, name):
    key = 'fxa-oauth.%s' % name
    return request.registry.settings[key]


def parse_clients(settings):
    resources = OrderedDict()
    scope_routing = {}

    for setting_key, setting_value in settings.items():
        if not setting_key.startswith('fxa-oauth.'):
            continue
        elif setting_key.startswith('fxa-oauth.clients.'):
            parts = setting_key.split('.', 4)
            client_name, setting_basename = parts[2:]
        else:
            _, setting_basename = setting_key.split('.', 1)
            client_name = "default"

        if setting_basename == 'required_scope':
            if setting_value in scope_routing:
                message = '{} is already required for another config.'.format(setting_value)
                raise ConfigurationError(message)
            if setting_value is not None:
                scope_routing[setting_value] = client_name

        resource = resources.setdefault(client_name, OrderedDict())
        resource[setting_basename] = setting_value

    return resources, scope_routing
