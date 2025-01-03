from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Q
from products.models import Product
from analytics.models import SearchQuery as SearchQueryLog

class SearchService:
    @staticmethod
    def search_products(query_text, user=None):
        # Create search vector
        search_vector = (
            SearchVector('name', weight='A') +
            SearchVector('description', weight='B') +
            SearchVector('category__name', weight='C')
        )
        
        # Create search query
        search_query = SearchQuery(query_text)
        
        # Get results with ranking
        results = Product.objects.annotate(
            rank=SearchRank(search_vector, search_query)
        ).filter(
            Q(rank__gte=0.1) |  # Matches from full-text search
            Q(name__icontains=query_text) |  # Direct matches in name
            Q(tags__name__icontains=query_text)  # Matches in tags
        ).order_by('-rank')
        
        # Log the search query
        SearchQueryLog.objects.create(
            user=user,
            query=query_text,
            results_count=results.count()
        )
        
        return results
    
    @staticmethod
    def get_related_products(product):
        """Get related products based on categories and tags"""
        return Product.objects.filter(
            Q(category=product.category) |
            Q(tags__in=product.tags.all())
        ).exclude(id=product.id).distinct()[:5]
    
    @staticmethod
    def get_trending_searches(days=7):
        """Get trending search queries from the past n days"""
        from django.utils import timezone
        from django.db.models import Count
        from datetime import timedelta
        
        return SearchQueryLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(days=days)
        ).values('query').annotate(
            count=Count('query')
        ).order_by('-count')[:10]
