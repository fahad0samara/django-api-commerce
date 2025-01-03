from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

from .models import UserProductInteraction, ProductSimilarity, UserPreferences
from products.models import Product

class RecommendationService:
    INTERACTION_WEIGHTS = {
        'view': 1.0,
        'cart_add': 2.0,
        'purchase': 3.0,
        'wishlist': 1.5,
        'review': 2.5,
    }
    
    @classmethod
    def record_interaction(cls, user, product, interaction_type):
        """Record a user's interaction with a product"""
        weight = cls.INTERACTION_WEIGHTS.get(interaction_type, 1.0)
        UserProductInteraction.objects.create(
            user=user,
            product=product,
            interaction_type=interaction_type,
            weight=weight
        )
    
    @classmethod
    def get_personalized_recommendations(cls, user, limit=10):
        """Get personalized product recommendations for a user"""
        cache_key = f'user_recommendations_{user.id}'
        recommendations = cache.get(cache_key)
        
        if recommendations is None:
            # Get user's interaction history
            interactions = UserProductInteraction.objects.filter(
                user=user
            ).values('product').annotate(
                total_weight=Sum('weight')
            ).order_by('-total_weight')
            
            # Get similar products
            product_ids = [i['product'] for i in interactions[:5]]
            similar_products = ProductSimilarity.objects.filter(
                product_a__in=product_ids
            ).select_related('product_b').order_by('-similarity_score')
            
            # Get user preferences
            preferences = UserPreferences.objects.filter(user=user).first()
            
            # Build recommendations considering both similarity and preferences
            recommendations = cls._build_recommendations(
                similar_products, preferences, limit
            )
            
            # Cache the results
            cache.set(cache_key, recommendations, 3600)  # Cache for 1 hour
        
        return recommendations
    
    @classmethod
    def update_product_similarities(cls):
        """Update product similarity scores"""
        # Get all products and their features
        products = Product.objects.all()
        
        # Create feature matrix
        features = cls._create_feature_matrix(products)
        
        # Calculate similarities
        similarities = cosine_similarity(features)
        
        # Update database
        batch_size = 1000
        similarity_objects = []
        
        for i in range(len(products)):
            for j in range(i + 1, len(products)):
                if similarities[i][j] > 0.1:  # Only store significant similarities
                    similarity_objects.append(
                        ProductSimilarity(
                            product_a=products[i],
                            product_b=products[j],
                            similarity_score=float(similarities[i][j])
                        )
                    )
                
                if len(similarity_objects) >= batch_size:
                    ProductSimilarity.objects.bulk_create(
                        similarity_objects,
                        ignore_conflicts=True
                    )
                    similarity_objects = []
        
        if similarity_objects:
            ProductSimilarity.objects.bulk_create(
                similarity_objects,
                ignore_conflicts=True
            )
    
    @staticmethod
    def _create_feature_matrix(products):
        """Create a feature matrix for products"""
        # Example features: category, price range, tags, etc.
        features = []
        for product in products:
            product_features = [
                product.category_id,
                float(product.price),
                product.brand_id if hasattr(product, 'brand_id') else 0,
            ]
            # Add tag features
            tags = product.tags.values_list('id', flat=True)
            product_features.extend(tags)
            features.append(product_features)
        
        return csr_matrix(features)
    
    @staticmethod
    def _build_recommendations(similar_products, preferences, limit):
        """Build final recommendations considering user preferences"""
        recommendations = []
        seen_products = set()
        
        for similarity in similar_products:
            product = similarity.product_b
            
            # Skip if we've seen this product or if it doesn't match preferences
            if product.id in seen_products or not preferences:
                continue
            
            # Apply preference filters
            if preferences:
                if preferences.price_range_max and product.price > preferences.price_range_max:
                    continue
                if preferences.price_range_min and product.price < preferences.price_range_min:
                    continue
                if preferences.favorite_categories.exists() and \
                   product.category not in preferences.favorite_categories.all():
                    continue
            
            recommendations.append(product)
            seen_products.add(product.id)
            
            if len(recommendations) >= limit:
                break
        
        return recommendations
