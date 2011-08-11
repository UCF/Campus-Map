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
			
			# check to see if they're the same
			for k,v in nb['properties'].items():
				if not ob['properties'][k] == nb['properties'][k]:
					changed.append(ob['properties'])
					changed.append(nb['properties'])
					break
			
			# item exists in old data, remove from both
			new['features'].remove(nb)
			old['features'].remove(ob)
			break

print "{0}\n  Updated Buildings \n{0}".format("-"*78)
for i in range(0, len(changed), 2):
	print changed[i]
	print changed[i+1]
	print

print "{0}\n  Needs Merging \n{0}".format("-"*78)
for nb in new['features'][:]:
	for ob in old['features']:
		if ob['properties']['Name'] == nb['properties']['Name']:
			print ob['properties']['Name']
			print " ", ob['properties']
			print " ", nb['properties']
			print
			old['features'].remove(ob)
			new['features'].remove(nb)
			break

print "\n{0}\n  New Buildings \n{0}".format("-"*78)
for nb in new['features']:
	print nb['properties']

print "\n\n{0}\n  Deleted Buildings \n{0}".format("-"*78)
for ob in old['features']:
	print ob['properties']