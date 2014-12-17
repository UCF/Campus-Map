# fix admin templates
from django.contrib.admin import site
site.index_template = 'admin/index.djt'
site.login_template = 'admin/login.djt'
