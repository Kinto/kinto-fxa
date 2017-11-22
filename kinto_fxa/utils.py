from pyramid.exceptions import ConfigurationError
from collections import OrderedDict


def fxa_conf(request, name):
    key = 'fxa-oauth.%s' % name
    return request.registry.settings[key]


def parse_resources(settings):
    resources = OrderedDict()
    scope_routing = {}

    for setting_key, setting_value in settings.items():
        if not setting_key.startswith('fxa-oauth.'):
            continue
        parts = setting_key.split('.', 3)
        if len(parts) == 2:  # default settings
            client_name = 'default'
            _, setting_basename = parts
        else:
            _, client_name, setting_basename = parts

        if setting_basename == 'required_scope':
            if setting_value in scope_routing:
                message = '{} is already required for another config.'.format(setting_value)
                raise ConfigurationError(message)
            if setting_value is not None:
                scope_routing[setting_value] = client_name

        if client_name in ('relier', 'state', 'webapp'):
            setting_basename = '{}.{}'.format(client_name, setting_basename)
            client_name = 'default'

        resource = resources.setdefault(client_name, OrderedDict())
        resource[setting_basename] = setting_value

    return resources, scope_routing
