from django import forms
from .models import Ticket, TicketMessage

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['subject', 'description', 'priority', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class TicketMessageForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        } 