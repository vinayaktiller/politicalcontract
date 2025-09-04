# utils.py (new file)
from users.models import Petitioner
from blog.models import BlogLoad

def update_blog_load_for_offline_user(user_id, blog_id):
    """Update BlogLoad for offline users when blog interactions happen"""
    try:
        user_obj = Petitioner.objects.get(id=user_id)
        if not user_obj.is_online:
            # Add to modified_blogs for offline users
            blog_load, created = BlogLoad.objects.get_or_create(
                userid=user_id,
                defaults={
                    'modified_blogs': [blog_id],
                    'new_blogs': [],
                    'loaded_blogs': [],
                    'outdated': True
                }
            )
            if not created:
                # Add blog to modified_blogs if not already present
                if blog_id not in blog_load.modified_blogs:
                    blog_load.modified_blogs.append(blog_id)
                    blog_load.outdated = True
                    blog_load.save()
            return True
    except Petitioner.DoesNotExist:
        print(f"User with ID {user_id} does not exist")
    return False