# importing settings 
from django.conf import settings

def aws_media(request):
    return {'MEDIA_URL':settings.MEDIA_URL}