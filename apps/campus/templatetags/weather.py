from django import template
from django.core.cache import cache

def weather(json_request = False):
	'''
	Yahoo Weather
	'''
	w = cache.get('yahoo_weather')
	if w is not None:
		if json_request:
			return cache.get('yahoo_weather_json')
		else:
			return { 'weather': w }
	
	import urllib, re
	try:
		
		f = urllib.urlopen("http://weather.yahoo.com/pbadge/?id=2466256&u=f&t=trans&l=navigation")
		c = f.read()
		f.close()
		
		# OCD about HTML validation (acronym obsolete)
		c = c.replace("acronym", "abbr")
		c = re.sub(r'&(site|promo|cm)', r'&amp;\1', c)
		
		# was: text description + weather channel icon linking to extended forecast
		# now: description linking to extended forecast
		fix = re.search(r'</abbr></span>(.+)&nbsp;&nbsp;', c)
		if fix is not None:
			c = re.sub(r'</abbr></span>(.+)&nbsp;&nbsp;', '</abbr></span>&nbsp;&nbsp;', c)
			description = fix.group(1)
			c = re.sub('<span class="efc"></span>', description, c)
		else:
			return { 'weather': None, 'error':'Error parsing weather content' }
		
		# fill json request
		find = re.search(r'<span>(\d+)<abbr title="Degree">', c)
		if find is None:
			temp = "Error"
		else:
			temp = find.group(1)
		
		w_json = { "temperature" : u'{0}\u00B0F'.format(temp), "description":description }
			
		# grab just icon and description
		w = re.search('(<div class="navweatherimage[\s\S]+</div>)\s*(<div class="discription">[\s\S]+</div>)\s*<div class="floatright">', c)
		if w is not None:
			w = "%s %s</div>" % ( w.group(1), w.group(2) )
		else:
			return { 'weather': None, 'error':'Error parsing weather content' }
	
	except IOError:
		return { 'weather': None, 'error':'IOError with opening URL' }

	cache.set('yahoo_weather', w)
	cache.set('yahoo_weather_json', w_json)
	
	if json_request:
		return w_json
	else:
		return { 'weather': w }

register = template.Library()
register.inclusion_tag("templatetags/weather.html")(weather)
