from ...models.Circle import Circle

from ...models.usertree import UserTree
from django.db.models import F

def create_connection_circles(notification):
    """
    Creates two Circle instances and updates the connection_count for the applicant and connection.
    """
    try:
        # Create Circle instance for applicant
        circle_1 = Circle.objects.create(
            userid=notification.applicant.id,
            otherperson=notification.connection.id,
            onlinerelation="connections"
        )

        # Create Circle instance for connection
        circle_2 = Circle.objects.create(
            userid=notification.connection.id,
            otherperson=notification.applicant.id,
            onlinerelation="connections"
        )
        # Update connection count for both users
        UserTree.objects.filter(id=notification.applicant.id).update(connection_count=F('connection_count') + 1)
        UserTree.objects.filter(id=notification.connection.id).update(connection_count=F('connection_count') + 1)
        

        print(f"Created Circles: {circle_1}, {circle_2}")
        print(f"Updated connection count for Applicant ID {notification.applicant.id} and Connection ID {notification.connection.id}")

        return circle_1, circle_2

    except Exception as e:
        print(f"Error creating connection circles: {e}")
        return None, None
