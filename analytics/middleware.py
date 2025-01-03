from .models import PageView
from django.utils.deprecation import MiddlewareMixin

class AnalyticsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.path.startswith('/admin/') and not request.path.startswith('/static/'):
            PageView.objects.create(
                user=request.user if request.user.is_authenticated else None,
                ip_address=self.get_client_ip(request),
                url=request.path,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referrer=request.META.get('HTTP_REFERER', None)
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
