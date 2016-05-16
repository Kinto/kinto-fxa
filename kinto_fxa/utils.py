def fxa_conf(request, name):
    key = 'fxa-oauth.%s' % name
    return request.registry.settings[key]
