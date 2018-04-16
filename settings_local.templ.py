# production:
#DEBUG                      = False
#TEMPLATE_DEBUG             = DEBUG

# development
DEBUG                      = True
TEMPLATE_DEBUG             = DEBUG

ALLOWED_HOSTS = ['map.ucf.edu', 'www.map.ucf.edu']
USE_X_FORWARDED_HOST = True

ADMINS         = (
    #('Your Name', 'your_email@domain.com'),
)
MANAGERS       = ADMINS

# Email settings for mailing forgot password emails
EMAIL_HOST          = ''
EMAIL_PORT          =

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/adminmedia/'

# Make this unique, and don't share it with anybody.
# http://www.miniwebtool.com/django-secret-key-generator/
SECRET_KEY = '**************************************************'

DATABASES = {
    'default': {
        'ENGINE'   : 'django.db.backends.sqlite3',   # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME'     : 'data/map.sqlite3.db',          # Or path to database file if using sqlite3, ex: data/sqlite3.db
        'USER'     : '',                             # Not used with sqlite3.
        'PASSWORD' : '',                             # Not used with sqlite3.
        'HOST'     : '',                             # Set to empty string for localhost. Not used with sqlite3.
        'PORT'     : '',                             # Set to empty string for default. Not used with sqlite3.
    }
}

# Only use if you want to override the default logging in settings.py
import os
PROJECT_FOLDER    = os.path.dirname(os.path.abspath(__file__))

LOGGING = {
    'version':1,
    'disable_existing_loggers':True,
    'filters': {
        'require_debug_true': {
            '()': 'logs.RequiredDebugTrue',
        },
        'require_debug_false': {
            '()': 'logs.RequiredDebugFalse',
        }
    },
    'formatters': {
        'concise': {
            'format':'\t'.join(['%(levelname)s','%(asctime)s','%(message)s']),
        },
        'talkative': {
            'format':'\t'.join(['%(levelname)s','%(asctime)s','%(funcName)s','%(lineno)d','%(message)s']),
        },
        # Request Specific Formatters
        'request_console_formatter':{
            'format':'\t'.join(['%(levelname)s','%(asctime)s','%(message)s','%(exc_info)s']),
        },
        'request_file_formatter':{
            'format':'\t'.join(['%(levelname)s','%(asctime)s','%(message)s','%(exc_info)s']),
        },
    },
    'handlers': {
        'discard': {
            'level' : 'DEBUG',
            'class' : 'django.utils.log.NullHandler'
        },
        'console': {
            'level'     : 'DEBUG',
            'class'     : 'logging.StreamHandler',
            'formatter' : 'concise',
            'filters'   : ['require_debug_true']
        },
        'file': {
            'level'       : 'DEBUG',
            'class'       : 'logging.handlers.RotatingFileHandler',
            'filename'    : '%s/application.log' % os.path.join(PROJECT_FOLDER, 'logs'),
            'maxBytes'    : 1024*1024*10, # 10 MB
            'backupCount' : 5,
            'formatter'   : 'concise',
            'filters'     : ['require_debug_false']
        },
        # Request Specific Handlers
        'console_request': {
            'level'       : 'DEBUG',
            'class'       : 'logging.StreamHandler',
            'formatter'   : 'request_console_formatter',
            'filters'     : ['require_debug_true']
        },
        'file_request': {
            'level'       : 'DEBUG',
            'class'       : 'logging.handlers.RotatingFileHandler',
            'filename'    : '%s/request.log' % os.path.join(PROJECT_FOLDER, 'logs'),
            'maxBytes'    : 1024*1024*10, # 10 MB
            'backupCount' : 5,
            'formatter'   : 'request_file_formatter',
            'filters'     : ['require_debug_false']
        }
    },
    'loggers': {
        'django.db.backends': { # Supress SQL debug messages
            'handlers'  : ['discard'],
            'level'     : 'DEBUG',
            'propagate' : False
        },
        'django.request': {
            'handlers'  : ['console_request', 'file_request'],
            'level'     : 'DEBUG',
            'propagate' : False
        },
        '': {
            'handlers'  : ['console', 'file'],
            'level'     : 'DEBUG',
            'propagate' : False
        },
    }
}

# Read settings.py for more details about these settings
#GOOGLE_CAN_SEE_ME = False
#GOOGLE_LOOK_HERE  = "https://map.ucf.edu"

# Weather data URL
WEATHER_URL = 'https://weather.smca.ucf.edu'

# Hoefler & Co Cloud.Typography Web Fonts url
# e.g. //cloud.typography.com/730568/6694752/css/fonts.css
CLOUD_TYPOGRAPHY_URL = None

# Secure HTTPS / SSL
HTTPS_SUPPORT = True
SECURE_REQUIRED_PATHS = [
    '/admin/',
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = HTTPS_SUPPORT
CSRF_COOKIE_SECURE = HTTPS_SUPPORT

REQUEST_TIMEOUT = 10
