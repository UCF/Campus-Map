import os

DEBUG = True

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
        'NAME'     : os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/map.sqlite3.db'), # Or path to database file if using sqlite3, ex: data/sqlite3.db
        'USER'     : '',                             # Not used with sqlite3.
        'PASSWORD' : '',                             # Not used with sqlite3.
        'HOST'     : '',                             # Set to empty string for localhost. Not used with sqlite3.
        'PORT'     : '',                             # Set to empty string for default. Not used with sqlite3.
    }
}

# Read settings.py for more details about these settings
#GOOGLE_CAN_SEE_ME = False
#GOOGLE_LOOK_HERE  = "https://map.ucf.edu"

# Weather data URL
WEATHER_URL = 'http://weather.smca.ucf.edu'

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

GOOGLE_API_KEY = ''

GA_ACCOUNT = ''

LOCATION_REDIRECT_BASE = 'https://www.ucf.edu/location/'

REDIRECT_TYPES = [
    'Location',
    'DiningLocation',
    'Building'
]

# Phonebook search service url
PHONEBOOK = 'https://search.cm.ucf.edu/api/v1/teledata/'
