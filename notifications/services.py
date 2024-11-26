from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification

def send_notification(user, notification_type, title, message):
    # Create notification in database
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message
    )
    
    # Send real-time notification
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'user_{user.id}_notifications',
        {
            'type': 'notify',
            'data': {
                'id': notification.id,
                'type': notification_type,
                'title': title,
                'message': message,
                'created': notification.created.isoformat()
            }
        }
    ) 