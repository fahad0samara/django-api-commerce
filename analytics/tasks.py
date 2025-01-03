from celery import shared_task
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import PageView, UserActivity, SearchQuery

@shared_task
def generate_daily_analytics_report():
    """Generate and email daily analytics report"""
    yesterday = timezone.now() - timedelta(days=1)
    
    # Page views analytics
    page_views = PageView.objects.filter(
        timestamp__date=yesterday.date()
    )
    
    popular_pages = page_views.values('url').annotate(
        views=Count('id')
    ).order_by('-views')[:10]
    
    # Search analytics
    searches = SearchQuery.objects.filter(
        timestamp__date=yesterday.date()
    )
    
    popular_searches = searches.values('query').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # User activity
    user_activities = UserActivity.objects.filter(
        timestamp__date=yesterday.date()
    )
    
    activity_summary = user_activities.values('action').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Create report
    report = f"""
    Daily Analytics Report for {yesterday.date()}
    
    Page Views Summary:
    ------------------
    Total Views: {page_views.count()}
    
    Top Pages:
    {'\n'.join([f"- {p['url']}: {p['views']} views" for p in popular_pages])}
    
    Search Summary:
    --------------
    Total Searches: {searches.count()}
    
    Popular Searches:
    {'\n'.join([f"- {s['query']}: {s['count']} times" for s in popular_searches])}
    
    User Activity Summary:
    --------------------
    {'\n'.join([f"- {a['action']}: {a['count']} times" for a in activity_summary])}
    """
    
    # Send email
    send_mail(
        subject=f"Daily Analytics Report - {yesterday.date()}",
        message=report,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[admin[1] for admin in settings.ADMINS],
        fail_silently=False,
    )

@shared_task
def cleanup_old_analytics_data():
    """Clean up analytics data older than 90 days"""
    cutoff_date = timezone.now() - timedelta(days=90)
    
    PageView.objects.filter(timestamp__lt=cutoff_date).delete()
    SearchQuery.objects.filter(timestamp__lt=cutoff_date).delete()
    
@shared_task
def update_search_analytics():
    """Update search analytics for trending searches"""
    from django.core.cache import cache
    
    # Get trending searches from the last 7 days
    last_week = timezone.now() - timedelta(days=7)
    trending_searches = SearchQuery.objects.filter(
        timestamp__gte=last_week
    ).values('query').annotate(
        count=Count('id')
    ).order_by('-count')[:20]
    
    # Cache the results
    cache.set('trending_searches', list(trending_searches), 3600)  # Cache for 1 hour
