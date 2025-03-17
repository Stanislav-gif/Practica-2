from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List
from datetime import datetime

# Создание базы данных и модели
DATABASE_URL = "sqlite:///./food_delivery.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class FoodItem(Base):
    __tablename__ = "food_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    delivery_time = Column(DateTime) 

Base.metadata.create_all(bind=engine)

# Модели Pydantic для валидации
class FoodItemCreate(BaseModel):
    name: str
    price: float
    delivery_time: datetime  #datetime для валидации

class FoodItemUpdate(BaseModel):
    name: str = None
    price: float = None
    delivery_time: datetime = None  #Обновление времени доставки

class FoodItemResponse(BaseModel):
    id: int
    name: str
    price: float
    delivery_time: datetime  # Время доставки в ответе

    class Config:
        orm_mode = True

app = FastAPI()

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/food_items/", response_model=List[FoodItemResponse])
def read_food_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    food_items = db.query(FoodItem).offset(skip).limit(limit).all()
    return food_items

@app.get("/food_items/{food_item_id}", response_model=FoodItemResponse)
def read_food_item(food_item_id: int, db: Session = Depends(get_db)):
    food_item = db.query(FoodItem).filter(FoodItem.id == food_item_id).first()
    if food_item is None:
        raise HTTPException(status_code=404, detail="Food item not found")
    return food_item

@app.post("/food_items/", response_model=FoodItemResponse)
def create_food_item(food_item: FoodItemCreate, db: Session = Depends(get_db)):
    db_food_item = FoodItem(**food_item.dict())
    db.add(db_food_item)
    db.commit()
    db.refresh(db_food_item)
    return db_food_item

@app.put("/food_items/{food_item_id}", response_model=FoodItemResponse)
def update_food_item(food_item_id: int, food_item: FoodItemUpdate, db: Session = Depends(get_db)):
    db_food_item = db.query(FoodItem).filter(FoodItem.id == food_item_id).first()
    if db_food_item is None:
        raise HTTPException(status_code=404, detail="Food item not found")
    
    for key, value in food_item.dict(exclude_unset=True).items():
        setattr(db_food_item, key, value)
    
    db.commit()
    db.refresh(db_food_item)
    return db_food_item

@app.delete("/food_items/{food_item_id}", status_code=204)
def delete_food_item(food_item_id: int, db: Session = Depends(get_db)):
    db_food_item = db.query(FoodItem).filter(FoodItem.id == food_item_id).first()
    if db_food_item is None:
        raise HTTPException(status_code=404, detail="Food item not found")
    db.delete(db_food_item)
    db.commit()
    return None
