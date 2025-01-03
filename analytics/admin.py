from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import PageView, UserActivity, SearchQuery

@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ('url', 'user', 'ip_address', 'timestamp', 'user_agent_display')
    list_filter = ('timestamp', 'url')
    search_fields = ('url', 'ip_address', 'user__email')
    date_hierarchy = 'timestamp'
    
    def user_agent_display(self, obj):
        return format_html('<span title="{}">{}</span>', 
                         obj.user_agent, 
                         obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent)
    user_agent_display.short_description = 'User Agent'

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'content_type', 'timestamp')
    list_filter = ('action', 'timestamp', 'content_type')
    search_fields = ('user__email', 'action')
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'content_type')

@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'results_count', 'user', 'timestamp')
    list_filter = ('timestamp', 'results_count')
    search_fields = ('query', 'user__email')
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def changelist_view(self, request, extra_context=None):
        # Add some aggregate data
        response = super().changelist_view(request, extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
            
        metrics = {
            'total_searches': qs.count(),
            'avg_results': qs.aggregate(avg_results=models.Avg('results_count'))['avg_results'],
            'popular_queries': qs.values('query').annotate(
                count=Count('query')
            ).order_by('-count')[:5]
        }
        
        response.context_data.update(metrics)
        return response
