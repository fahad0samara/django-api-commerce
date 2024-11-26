from django.contrib import admin
from .models import Ticket, TicketMessage

class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ['created']

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'user', 'status', 'priority', 'created', 'updated']
    list_filter = ['status', 'priority', 'created']
    search_fields = ['subject', 'description', 'user__username']
    inlines = [TicketMessageInline]
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, TicketMessage):
                if not instance.pk:  # If it's a new message
                    instance.user = request.user
                    instance.is_staff_reply = True
            instance.save()
        formset.save_m2m() 