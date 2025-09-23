def get_profilepic_url(obj, request):
    if obj.profilepic and hasattr(obj.profilepic, 'url') and request is not None:
        return request.build_absolute_uri(obj.profilepic.url)
    return None
