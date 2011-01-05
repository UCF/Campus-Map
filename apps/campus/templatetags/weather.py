from django import template
from django.core.cache import cache

def weather():
	'''
	Yahoo Weather
	'''
	w = cache.get('yahoo_weather')
	if w is not None:
		return { 'weather': w }
	
	import urllib, re
	try:
		f = urllib.urlopen("http://weather.yahoo.com/pbadge/?id=2466256&u=f&t=trans&l=navigation")
		c = f.read()
		f.close()
		
		# was: text description + weather channel icon linking to extended forecast
		# now: description linking to extended forecast
		fix = re.search('</acronym></span>(.+)&nbsp;&nbsp;', c)
		if fix is not None:
			c = re.sub('</acronym></span>(.+)&nbsp;&nbsp;', '</acronym></span>&nbsp;&nbsp;', c)
			c = re.sub('<span class="efc"></span>', fix.group(1), c)
		
		# grab just icon and description
		w = re.search('(<div class="navweatherimage[\s\S]+</div>)\s*(<div class="discription">[\s\S]+</div>)\s*<div class="floatright">', c)
		if w is not None:
			w = "%s %s</div>" % ( w.group(1), w.group(2) )
		else:
			return { 'weather': None, 'error':'Error parsing weather content' }
	
	except IOError:
		return { 'weather': None, 'error':'IOError with opening URL' }

	cache.set('yahoo_weather', w)
	return { 'weather': w }

register = template.Library()
register.inclusion_tag("templatetags/weather.html")(weather)
