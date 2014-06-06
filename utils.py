import logging

from django.test.runner import DiscoverRunner

class DisableLoggingTestRunner(DiscoverRunner):
    def run_tests(self, test_labels, extra_tests=None, **kwargs):

        # don't show logging messages while testing
        logging.disable(logging.CRITICAL)

        return super(DisableLoggingTestRunner, self).run_tests(test_labels, extra_tests, **kwargs)
