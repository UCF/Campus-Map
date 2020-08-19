from time import time

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponsePermanentRedirect


class DisableCSRF(object):
    ''' sad panda '''
    def process_view(self, request, callback, callback_args, callback_kwargs):
        setattr(request, '_dont_enforce_csrf_checks', True)


class SecureRequiredMiddleware(object):
    def __init__(self):
        self.paths = getattr(settings, 'SECURE_REQUIRED_PATHS')
        self.enabled = self.paths and getattr(settings, 'HTTPS_SUPPORT')

    def process_request(self, request):
        if self.enabled and not request.is_secure():
            for path in self.paths:
                if request.get_full_path().startswith(path):
                    request_url = request.build_absolute_uri(request.get_full_path())
                    secure_url = request_url.replace('http://', 'https://')
                    return HttpResponsePermanentRedirect(secure_url)
        return None


def map_context(request):
    '''
    Context Processor
    '''
    context_extras = {}

    if settings.DEBUG:
        context_extras['map_version'] = str(time())
    else:
        context_extras['map_version'] = settings.MAP_VERSION

    base_url = request.build_absolute_uri(reverse('campus.views.home'))[:-1]
    context_extras['base_url'] = base_url

    if settings.CLOUD_TYPOGRAPHY_URL:
        context_extras['cloud_typography'] = settings.CLOUD_TYPOGRAPHY_URL

    context_extras['google_api_key'] = settings.GOOGLE_API_KEY

    return context_extras
