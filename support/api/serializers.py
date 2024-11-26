from rest_framework import serializers
from ..models import Ticket, TicketMessage

class TicketMessageSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TicketMessage
        fields = ['id', 'message', 'created', 'user_name', 'is_staff_reply']
        read_only_fields = ['created', 'is_staff_reply']

class TicketSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Ticket
        fields = ['id', 'subject', 'description', 'status', 'priority', 
                 'created', 'updated', 'order', 'messages']
        read_only_fields = ['created', 'updated'] 