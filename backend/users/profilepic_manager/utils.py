# def get_profilepic_url(obj, request):
#     if obj.profilepic and hasattr(obj.profilepic, 'url') and request is not None:
#         return request.build_absolute_uri(obj.profilepic.url)
#     return None

def get_profilepic_url(obj, request=None):
    if obj.profilepic and hasattr(obj.profilepic, 'url'):
        url = obj.profilepic.url
        if request:
            # Build absolute URL for local/dev environment
            return request.build_absolute_uri(url)
        else:
            # Just return relative URL (assumed it works for production setup)
            return url
    return None

