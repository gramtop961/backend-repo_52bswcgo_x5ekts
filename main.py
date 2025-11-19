import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order

app = FastAPI(title="Food E-commerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Food E-commerce Backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# Products endpoints
@app.post("/api/products", response_model=dict)
async def create_product(product: Product):
    try:
        new_id = create_document("product", product)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products", response_model=List[dict])
async def list_products(category: Optional[str] = None):
    try:
        filter_query = {"category": category} if category else {}
        docs = get_documents("product", filter_query)
        for d in docs:
            d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Seed some demo products if collection is empty
@app.post("/api/products/seed")
async def seed_products():
    try:
        existing = get_documents("product")
        if existing:
            return {"seeded": False, "count": len(existing)}
        demo = [
            {
                "title": "Margherita Pizza",
                "description": "Classic tomato, mozzarella, basil",
                "price": 9.99,
                "category": "Pizza",
                "image_url": "https://images.unsplash.com/photo-1548365328-9f547fb0953d",
                "rating": 4.7,
                "in_stock": True
            },
            {
                "title": "Cheeseburger",
                "description": "Juicy beef patty with cheddar",
                "price": 8.49,
                "category": "Burgers",
                "image_url": "https://images.unsplash.com/photo-1550547660-d9450f859349",
                "rating": 4.5,
                "in_stock": True
            },
            {
                "title": "Caesar Salad",
                "description": "Crisp romaine with parmesan",
                "price": 7.25,
                "category": "Salads",
                "image_url": "https://images.unsplash.com/photo-1568605114967-8130f3a36994",
                "rating": 4.3,
                "in_stock": True
            },
            {
                "title": "Iced Latte",
                "description": "Chilled espresso with milk",
                "price": 4.5,
                "category": "Drinks",
                "image_url": "https://images.unsplash.com/photo-1541167760496-1628856ab772",
                "rating": 4.6,
                "in_stock": True
            }
        ]
        for p in demo:
            create_document("product", p)
        return {"seeded": True, "count": len(demo)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Orders endpoints
@app.post("/api/orders", response_model=dict)
async def create_order(order: Order):
    try:
        # Basic validation: totals consistency
        computed_subtotal = sum(item.price * item.quantity for item in order.items)
        if abs(computed_subtotal - order.subtotal) > 0.01:
            raise HTTPException(status_code=400, detail="Subtotal does not match items total")
        total_calc = order.subtotal + order.tax
        if abs(total_calc - order.total) > 0.01:
            raise HTTPException(status_code=400, detail="Total does not match subtotal + tax")

        new_id = create_document("order", order)
        return {"id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders", response_model=List[dict])
async def list_orders():
    try:
        docs = get_documents("order")
        for d in docs:
            d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
