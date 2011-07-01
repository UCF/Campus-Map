from django import template

register = template.Library()

def highlight_term(s, t):
	s_l = s.lower()
	t_loc = s_l.find(t)
	if t_loc == -1:
		return s
	else:
		return ''.join([s[0:t_loc], '<span class="highlight">', s[t_loc:t_loc + len(t)], '</span>', s[t_loc + len(t):]])

register.filter('highlight_term', highlight_term)