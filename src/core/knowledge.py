"""
Knowledge Management System - Product & FAQ Management
منتظر - نظام إدارة المعرفة والمنتجات
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class Product:
    """Product data structure"""
    id: str
    name: str
    description: str
    price: int
    stock: int
    category: str
    attributes: List[str]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock": self.stock,
            "category": self.category,
            "attributes": self.attributes,
        }

    def to_summary(self) -> str:
        """Generate a concise summary for the product"""
        stock_status = "متوفر" if self.stock > 0 else "غير متوفر"
        return f"• {self.name}: {self.price:,} دينار ({stock_status})"


class KnowledgeManager:
    """
    Manages product knowledge for the AI agent.
    Handles CSV ingestion, product search, and knowledge retrieval.
    """

    def __init__(self, products_path: Optional[str] = None):
        self.products: Dict[str, Product] = {}
        self.products_df: Optional[pd.DataFrame] = None
        
        if products_path:
            self.load_products_csv(products_path)

    def load_products_csv(self, csv_path: str) -> bool:
        """Load products from a CSV file"""
        try:
            path = Path(csv_path)
            if not path.exists():
                print(f"Products file not found: {csv_path}")
                return False

            df = pd.read_csv(csv_path, encoding='utf-8')
            self.products_df = df
            self.products.clear()

            for _, row in df.iterrows():
                # Parse attributes (pipe-separated)
                attributes = []
                if pd.notna(row.get('attributes', '')):
                    attributes = str(row['attributes']).split('|')

                product = Product(
                    id=str(row['id']),
                    name=str(row['name']),
                    description=str(row.get('description', '')),
                    price=int(row.get('price', 0)),
                    stock=int(row.get('stock', 0)),
                    category=str(row.get('category', 'general')),
                    attributes=attributes,
                )
                self.products[product.id] = product

            print(f"Loaded {len(self.products)} products")
            return True

        except Exception as e:
            print(f"Error loading products: {e}")
            return False

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get a product by ID"""
        return self.products.get(product_id)

    def get_product_by_name(self, name: str) -> Optional[Product]:
        """Find a product by name (partial match)"""
        name_lower = name.lower()
        for product in self.products.values():
            if name_lower in product.name.lower():
                return product
        return None

    def search_products(
        self,
        query: str = "",
        category: str = "",
        max_price: int = 0,
        in_stock_only: bool = False,
    ) -> List[Product]:
        """Search products with filters"""
        results = []
        query_lower = query.lower()

        for product in self.products.values():
            # Apply filters
            if in_stock_only and product.stock <= 0:
                continue
            if max_price > 0 and product.price > max_price:
                continue
            if category and product.category.lower() != category.lower():
                continue

            # Text search in name, description, attributes
            if query:
                searchable = (
                    product.name.lower() +
                    product.description.lower() +
                    " ".join(product.attributes).lower()
                )
                if query_lower not in searchable:
                    continue

            results.append(product)

        return results

    def get_all_products(self) -> List[Product]:
        """Get all products"""
        return list(self.products.values())

    def get_products_by_category(self, category: str) -> List[Product]:
        """Get products in a specific category"""
        return [p for p in self.products.values() if p.category.lower() == category.lower()]

    def get_categories(self) -> List[str]:
        """Get all unique categories"""
        return list(set(p.category for p in self.products.values()))

    def get_product_summary(self, max_products: int = 10) -> str:
        """Generate a summary of products for the AI context"""
        products = list(self.products.values())[:max_products]
        summaries = [p.to_summary() for p in products]
        
        if len(self.products) > max_products:
            summaries.append(f"... و{len(self.products) - max_products} منتجات أخرى")
        
        return "\n".join(summaries)

    def get_product_details(self, product_id: str) -> str:
        """Get formatted product details for customer response"""
        product = self.get_product(product_id)
        if not product:
            return "المنتج غير موجود"

        stock_text = f"متوفر ({product.stock} قطعة)" if product.stock > 0 else "نفذ من المخزون"
        
        return f"""📦 {product.name}

📝 الوصف: {product.description}
💰 السعر: {product.price:,} دينار
📊 الحالة: {stock_text}
🏷️ الفئة: {product.category}
"""

    def check_stock(self, product_id: str) -> int:
        """Check stock for a product"""
        product = self.get_product(product_id)
        return product.stock if product else 0

    def get_price(self, product_id: str) -> int:
        """Get price for a product"""
        product = self.get_product(product_id)
        return product.price if product else 0

    def find_alternatives(self, product_id: str, limit: int = 3) -> List[Product]:
        """Find alternative products in the same category"""
        product = self.get_product(product_id)
        if not product:
            return []

        alternatives = [
            p for p in self.products.values()
            if p.category == product.category and p.id != product_id and p.stock > 0
        ]
        return alternatives[:limit]

    def get_cheapest_in_category(self, category: str) -> Optional[Product]:
        """Get the cheapest product in a category"""
        products = self.get_products_by_category(category)
        if not products:
            return None
        return min(products, key=lambda p: p.price)

    def get_most_expensive_in_category(self, category: str) -> Optional[Product]:
        """Get the most expensive product in a category"""
        products = self.get_products_by_category(category)
        if not products:
            return None
        return max(products, key=lambda p: p.price)
