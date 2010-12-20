from django.views.generic.simple import direct_to_template

def example_view(request):
	content = "ohai - this is a sample view"
	return direct_to_template(request, 'example.djt', locals())