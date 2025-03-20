from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional

# Создание базы данных и модели
DATABASE_URL = "sqlite:///./bakery_items.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class BakeryItem(Base):
    __tablename__ = "bakery_items" 
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)

Base.metadata.create_all(bind=engine)

# Модели Pydantic для валидации
class BakeryItemCreate(BaseModel):
    name: str
    description: str
    price: float

class BakeryItemUpdate(BaseModel):
    name: Optional[str] = None  # Optional для опциональных полей
    description: Optional[str] = None
    price: Optional[float] = None

class BakeryItemResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float

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

@app.get("/bakery_items/", response_model=List[BakeryItemResponse])
def read_bakery_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    bakery_items = db.query(BakeryItem).offset(skip).limit(limit).all()
    return bakery_items

@app.get("/bakery_items/{item_id}", response_model=BakeryItemResponse)
def read_bakery_item(item_id: int, db: Session = Depends(get_db)):
    bakery_item = db.query(BakeryItem).filter(BakeryItem.id == item_id).first()
    if bakery_item is None:
        raise HTTPException(status_code=404, detail="Bakery item not found")
    return bakery_item

@app.post("/bakery_items/", response_model=BakeryItemResponse)
def create_bakery_item(bakery_item: BakeryItemCreate, db: Session = Depends(get_db)):
    db_bakery_item = BakeryItem(**bakery_item.dict())
    db.add(db_bakery_item)
    db.commit()
    db.refresh(db_bakery_item)
    return db_bakery_item

@app.put("/bakery_items/{item_id}", response_model=BakeryItemResponse)
def update_bakery_item(item_id: int, bakery_item: BakeryItemUpdate, db: Session = Depends(get_db)):
    db_bakery_item = db.query(BakeryItem).filter(BakeryItem.id == item_id).first()
    if db_bakery_item is None:
        raise HTTPException(status_code=404, detail="Bakery item not found")
    
    for key, value in bakery_item.dict(exclude_unset=True).items():
        setattr(db_bakery_item, key, value)
    
    db.commit()
    db.refresh(db_bakery_item)
    return db_bakery_item

@app.delete("/bakery_items/{item_id}", status_code=204)
def delete_bakery_item(item_id: int, db: Session = Depends(get_db)):
    db_bakery_item = db.query(BakeryItem).filter(BakeryItem.id == item_id).first()
    if db_bakery_item is None:
        raise HTTPException(status_code=404, detail="Bakery item not found")
    db.delete(db_bakery_item)
    db.commit()
    return None
