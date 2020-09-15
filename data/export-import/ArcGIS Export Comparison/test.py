import sys, os, json, copy


''' open and load exports '''
text = open('new_shp_export.json', 'r').read()
new = json.loads(text)
text = open('old_shp_export.json', 'r').read()
old = json.loads(text)

''' sort buildings '''
new['features'] = sorted(new['features'], key=lambda i:i['properties']['Num'])
old['features'] = sorted(old['features'], key=lambda i:i['properties']['Num'])


changed = []
deleted_new = []
deleted_old = []

for nb in new['features'][:]:
	
	# look for it in old
	for ob in old['features']:
		
		if ob['properties']['Num'] == nb['properties']['Num']:
			if ob['geometry'] != nb['geometry']:
				print((ob['properties']['Name']))
				print((" ", ob['geometry']))
				print((" ", nb['geometry']))
			old['features'].remove(ob)
			new['features'].remove(nb)
			break

print(("\n{0}\n  New Buildings \n{0}".format("-"*78)))
for nb in new['features']:
	print((nb['properties']['Name'], nb['geometry']))

print(("\n\n{0}\n  Deleted Buildings \n{0}".format("-"*78)))
for ob in old['features']:
	print((ob['properties']['Name'], ob['geometry']))