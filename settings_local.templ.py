DEBUG          = True
TEMPLATE_DEBUG = DEBUG
TEMPLATE_STRING_IF_INVALID = 'halp!'

ADMINS         = (
	#('Your Name', 'your_email@domain.com'),
)
MANAGERS       = ADMINS

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/adminmedia/'

# Make this unique, and don't share it with anybody.
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

# INTERNAL_IPS = ['127.0.0.1',]


# For Google to render KML layers, it needs to import the map data.  If working
# locally or behind a firewall, this will not be possible.  If GOOGLE_CAN_SEE_ME
# if false, will fall back to GOOGLE_LOOK_HERE (leave off trailing slash)
GOOGLE_CAN_SEE_ME = True
GOOGLE_LOOK_HERE  = "http://map.ucf.edu"


# TODO: open all data to be indexed by a real search engine, otherwise
# search returns a very basic (nearly useless) keymatch result
SEARCH_ENGINE = None


# Phonebook search service url
PHONEBOOK = "http://webcom.dev.smca.ucf.edu/people/service.php"
