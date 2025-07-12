"""
Data Normalizer for RetailMate
Converts raw API responses to unified models
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..api_clients.user_apis.dummyjson_client import DummyJSONUsersClient
from ..api_clients.product_apis.fake_store_client import FakeStoreAPIClient
from ..api_clients.product_apis.dummyjson_products_client import DummyJSONProductsClient
from ...models.unified_models.product_models import (
    UnifiedProduct, ProductRating, ProductDimensions, 
    ProductReview, ProductAvailability, ProductCollection, ProductCategory
)
from ...models.unified_models.user_models import (
    UnifiedUser, UserLocation, UserContact, ShoppingPreferences,
    BudgetRange, ShoppingStyle, GenderType, UserCollection
)

logger = logging.getLogger("retailmate-data-normalizer")

class DataNormalizer:
    """Normalizes data from different APIs into unified models"""
    
    def __init__(self):
        self.logger = logging.getLogger("retailmate-normalizer")
        
    def normalize_fake_store_product(self, raw_product: Dict[str, Any]) -> UnifiedProduct:
        """Normalize Fake Store API product to unified model"""
        try:
            # Handle rating
            rating = None
            if raw_product.get('rating'):
                rating = ProductRating(
                    average=raw_product['rating'].get('rate', 0),
                    count=raw_product['rating'].get('count', 0),
                    source="fake_store"
                )
            # Normalized category
            category = raw_product.get('category', '').lower()
            category_map = {
                "beauty": ProductCategory.BEAUTY,
                "electronics": ProductCategory.ELECTRONICS,
                "men's clothing": ProductCategory.CLOTHING_MENS,
                "mens-clothing": ProductCategory.CLOTHING_MENS,
                "women's clothing": ProductCategory.CLOTHING_WOMENS,
                "womens-clothing": ProductCategory.CLOTHING_WOMENS,
                "jewelery": ProductCategory.JEWELRY,
                "jewelry": ProductCategory.JEWELRY,
                "home-decoration": ProductCategory.HOME,
                "furniture": ProductCategory.FURNITURE,
                "groceries": ProductCategory.GROCERIES,
                "kitchen-accessories": ProductCategory.KITCHEN,
                "sports-accessories": ProductCategory.SPORTS,
            }
            normalized_category = category_map.get(category, ProductCategory.ELECTRONICS)
            # Embedding text
            embedding_text = ' '.join(filter(None, [
                raw_product.get('title', ''),
                raw_product.get('description', ''),
                raw_product.get('category', ''),
                raw_product.get('brand', ''),
                raw_product.get('tags', []),
            ]))
            if isinstance(raw_product.get('tags', []), list):
                embedding_text = ' '.join(filter(None, [
                    raw_product.get('title', ''),
                    raw_product.get('description', ''),
                    raw_product.get('category', ''),
                    raw_product.get('brand', ''),
                    ' '.join(raw_product.get('tags', []))
                ]))
            # Create unified product
            product = UnifiedProduct(
                id=f"fake_store_{raw_product['id']}",
                source_api="fake_store",
                title=raw_product.get('title', ''),
                description=raw_product.get('description', ''),
                category=raw_product.get('category', ''),
                normalized_category=normalized_category,
                price=float(raw_product.get('price', 0)),
                images=[raw_product.get('image', '')] if raw_product.get('image') else [],
                rating=rating,
                availability=ProductAvailability(
                    in_stock=True,
                    availability_status="In Stock"
                ),
                embedding_text=embedding_text
            )
            return product
        except Exception as e:
            self.logger.error(f"Error normalizing Fake Store product: {e}")
            raise

    def normalize_dummyjson_product(self, raw_product: Dict[str, Any]) -> UnifiedProduct:
        """Normalize DummyJSON product to unified model"""
        try:
            # Handle rating
            rating = None
            if raw_product.get('rating'):
                rating = ProductRating(
                    average=float(raw_product['rating']),
                    count=0,  # DummyJSON doesn't provide count directly
                    source="dummyjson"
                )
            # Handle dimensions
            dimensions = None
            if raw_product.get('dimensions'):
                dims = raw_product['dimensions']
                dimensions = ProductDimensions(
                    width=dims.get('width'),
                    height=dims.get('height'),
                    depth=dims.get('depth'),
                    weight=raw_product.get('weight')
                )
            # Handle reviews
            reviews = []
            if raw_product.get('reviews'):
                for review in raw_product['reviews'][:5]:  # Limit to 5 reviews
                    try:
                        review_obj = ProductReview(
                            reviewer_name=review.get('reviewerName', 'Anonymous'),
                            rating=review.get('rating', 3),
                            comment=review.get('comment', ''),
                            date=datetime.fromisoformat(review.get('date', '2024-01-01T00:00:00Z').replace('Z', '+00:00'))
                        )
                        reviews.append(review_obj)
                    except:
                        continue
            # Handle availability
            availability = ProductAvailability(
                in_stock=raw_product.get('stock', 0) > 0,
                stock_quantity=raw_product.get('stock'),
                availability_status=raw_product.get('availabilityStatus', 'Unknown')
            )
            # Calculate original price if discount exists
            price = float(raw_product.get('price', 0))
            discount_percent = raw_product.get('discountPercentage', 0)
            original_price = None
            if discount_percent > 0:
                original_price = price / (1 - discount_percent / 100)
            # Normalized category
            category = raw_product.get('category', '').lower()
            category_map = {
                "beauty": ProductCategory.BEAUTY,
                "electronics": ProductCategory.ELECTRONICS,
                "men's clothing": ProductCategory.CLOTHING_MENS,
                "mens-clothing": ProductCategory.CLOTHING_MENS,
                "women's clothing": ProductCategory.CLOTHING_WOMENS,
                "womens-clothing": ProductCategory.CLOTHING_WOMENS,
                "jewelery": ProductCategory.JEWELRY,
                "jewelry": ProductCategory.JEWELRY,
                "home-decoration": ProductCategory.HOME,
                "furniture": ProductCategory.FURNITURE,
                "groceries": ProductCategory.GROCERIES,
                "kitchen-accessories": ProductCategory.KITCHEN,
                "sports-accessories": ProductCategory.SPORTS,
            }
            normalized_category = category_map.get(category, ProductCategory.ELECTRONICS)
            # Embedding text
            embedding_text = ' '.join(filter(None, [
                raw_product.get('title', ''),
                raw_product.get('description', ''),
                raw_product.get('category', ''),
                raw_product.get('brand', ''),
                ' '.join(raw_product.get('tags', []))
            ]))
            # Create unified product
            product = UnifiedProduct(
                id=f"dummyjson_{raw_product['id']}",
                source_api="dummyjson",
                title=raw_product.get('title', ''),
                description=raw_product.get('description', ''),
                category=raw_product.get('category', ''),
                normalized_category=normalized_category,
                price=price,
                discount_percentage=discount_percent if discount_percent > 0 else None,
                original_price=original_price,
                images=raw_product.get('images', []),
                thumbnail=raw_product.get('thumbnail'),
                brand=raw_product.get('brand'),
                sku=raw_product.get('sku'),
                tags=raw_product.get('tags', []),
                rating=rating,
                reviews=reviews,
                dimensions=dimensions,
                availability=availability,
                embedding_text=embedding_text
            )
            return product
        except Exception as e:
            self.logger.error(f"Error normalizing DummyJSON product: {e}")
            raise

    def normalize_dummyjson_user(self, raw_user: Dict[str, Any]) -> UnifiedUser:
        """Normalize DummyJSON user to unified model"""
        try:
            # Handle location
            location = None
            if raw_user.get('address'):
                addr = raw_user['address']
                location = UserLocation(
                    city=addr.get('city'),
                    state=addr.get('state'),
                    country=addr.get('country')
                )
            # Handle contact
            contact = UserContact(
                email=raw_user.get('email'),
                phone=raw_user.get('phone')
            )
            # Derive shopping preferences
            age = raw_user.get('age', 25)
            gender = raw_user.get('gender', '').lower()
            # Map gender
            gender_mapped = GenderType.OTHER
            if gender == 'male':
                gender_mapped = GenderType.MALE
            elif gender == 'female':
                gender_mapped = GenderType.FEMALE
            # Derive budget range from age (simplified logic)
            budget = BudgetRange.MID_RANGE
            if age < 25:
                budget = BudgetRange.BUDGET
            elif age > 45:
                budget = BudgetRange.PREMIUM
            # Derive preferred categories
            preferred_categories = []
            if gender == 'female':
                preferred_categories.extend(['beauty', 'womens-clothing', 'jewelry'])
            elif gender == 'male':
                preferred_categories.extend(['mens-clothing', 'electronics', 'sports'])
            # Age-based categories
            if age < 30:
                preferred_categories.extend(['electronics', 'sports'])
            else:
                preferred_categories.extend(['home', 'furniture'])
            shopping_prefs = ShoppingPreferences(
                preferred_categories=list(set(preferred_categories)),
                budget_range=budget,
                shopping_style=ShoppingStyle.ONLINE
            )
            # Compose preference_text
            parts = []
            if age:
                parts.append(f"age {age}")
            if gender_mapped:
                parts.append(f"gender {gender_mapped}")
            if location:
                if location.city:
                    parts.append(f"from {location.city}")
                if location.country:
                    parts.append(f"country {location.country}")
            if shopping_prefs.preferred_categories:
                parts.append(f"likes {' '.join(shopping_prefs.preferred_categories)}")
            if shopping_prefs.budget_range:
                parts.append(f"budget {shopping_prefs.budget_range}")
            if shopping_prefs.shopping_style:
                parts.append(f"shops {shopping_prefs.shopping_style}")
            preference_text = ' '.join(parts) if parts else "general shopper"
            # Create unified user
            user = UnifiedUser(
                id=f"dummyjson_{raw_user['id']}",
                source_api="dummyjson",
                first_name=raw_user.get('firstName', ''),
                last_name=raw_user.get('lastName', ''),
                username=raw_user.get('username'),
                age=age,
                gender=gender_mapped,
                contact=contact,
                location=location,
                profile_image=raw_user.get('image'),
                shopping_preferences=shopping_prefs,
                preference_text=preference_text
            )
            return user
        except Exception as e:
            self.logger.error(f"Error normalizing DummyJSON user: {e}")
            raise
    
    async def normalize_all_products(self) -> ProductCollection:
        """Normalize products from all APIs"""
        all_products = []
        source_breakdown = {}
        
        # Get Fake Store products
        try:
            async with FakeStoreAPIClient() as client:
                fake_store_products = await client.get_products()
                
                for raw_product in fake_store_products:
                    product = self.normalize_fake_store_product(raw_product)
                    all_products.append(product)
                
                source_breakdown['fake_store'] = len(fake_store_products)
                self.logger.info(f"Normalized {len(fake_store_products)} Fake Store products")
                
        except Exception as e:
            self.logger.error(f"Error fetching Fake Store products: {e}")
            source_breakdown['fake_store'] = 0
        
        # Get DummyJSON products
        try:
            async with DummyJSONProductsClient() as client:
                response = await client.get_products(limit=100)
                dummyjson_products = response.get('products', [])
                
                for raw_product in dummyjson_products:
                    product = self.normalize_dummyjson_product(raw_product)
                    all_products.append(product)
                
                source_breakdown['dummyjson'] = len(dummyjson_products)
                self.logger.info(f"Normalized {len(dummyjson_products)} DummyJSON products")
                
        except Exception as e:
            self.logger.error(f"Error fetching DummyJSON products: {e}")
            source_breakdown['dummyjson'] = 0
        
        # Create category breakdown
        category_breakdown = {}
        for product in all_products:
            category = product.normalized_category.value
            category_breakdown[category] = category_breakdown.get(category, 0) + 1
        
        return ProductCollection(
            products=all_products,
            total_count=len(all_products),
            source_breakdown=source_breakdown,
            category_breakdown=category_breakdown
        )
    
    async def normalize_all_users(self) -> UserCollection:
        """Normalize users from all APIs"""
        all_users = []
        
        # Get DummyJSON users
        try:
            async with DummyJSONUsersClient() as client:
                response = await client.get_users(limit=30)
                dummyjson_users = response.get('users', [])
                
                for raw_user in dummyjson_users:
                    user = self.normalize_dummyjson_user(raw_user)
                    all_users.append(user)
                
                self.logger.info(f"Normalized {len(dummyjson_users)} DummyJSON users")
                
        except Exception as e:
            self.logger.error(f"Error fetching DummyJSON users: {e}")
        
        # Create demographics breakdown
        demographics = {
            'total_users': len(all_users),
            'gender_distribution': {},
            'age_distribution': {},
            'budget_distribution': {}
        }
        
        for user in all_users:
            # Gender distribution
            gender = user.gender.value if user.gender else 'unknown'
            demographics['gender_distribution'][gender] = demographics['gender_distribution'].get(gender, 0) + 1
            
            # Age distribution
            if user.age:
                age_group = '18-25' if user.age <= 25 else '26-40' if user.age <= 40 else '40+'
                demographics['age_distribution'][age_group] = demographics['age_distribution'].get(age_group, 0) + 1
            
            # Budget distribution
            budget = user.shopping_preferences.budget_range.value
            demographics['budget_distribution'][budget] = demographics['budget_distribution'].get(budget, 0) + 1
        
        return UserCollection(
            users=all_users,
            total_count=len(all_users),
            demographics_breakdown=demographics
        )
