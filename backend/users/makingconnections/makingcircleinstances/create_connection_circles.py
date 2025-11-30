from ...models.Circle import Circle

from ...models.usertree import UserTree
from django.db.models import F

def create_connection_circles(notification):
    """
    Creates two Circle instances and updates the connection_count for the applicant and connection.
    """
    try:
        # Create Circle instances
        circle_1 = Circle.objects.create(
            userid=notification.applicant.id,
            otherperson=notification.connection.id,
            onlinerelation="connections"
        )

        circle_2 = Circle.objects.create(
            userid=notification.connection.id,
            otherperson=notification.applicant.id,
            onlinerelation="connections"
        )
        
        # Update connection count and check milestones for both users
        applicant_tree = UserTree.objects.get(id=notification.applicant.id)
        connection_tree = UserTree.objects.get(id=notification.connection.id)
        
        # Use the increment method to ensure milestone checking
        applicant_tree.increment_connection_count()
        connection_tree.increment_connection_count()
        
        print(f"Created Circles: {circle_1}, {circle_2}")
        print(f"Updated connection count for Applicant ID {notification.applicant.id} and Connection ID {notification.connection.id}")

        return circle_1, circle_2

    except UserTree.DoesNotExist as e:
        print(f"UserTree not found: {e}")
        return None, None
    except Exception as e:
        print(f"Error creating connection circles: {e}")
        return None, None