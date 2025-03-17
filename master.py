from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List

# Создание базы данных и модели
DATABASE_URL = "sqlite:///./energy_drinks.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class EnergyDrink(Base):
    __tablename__ = "energy_drinks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)

Base.metadata.create_all(bind=engine)

# Модели Pydantic для валидации
class EnergyDrinkCreate(BaseModel):
    name: str
    price: float

class EnergyDrinkUpdate(BaseModel):
    name: str = None
    price: float = None

class EnergyDrinkResponse(BaseModel):
    id: int
    name: str
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

@app.get("/energy_drinks/", response_model=List[EnergyDrinkResponse])
def read_energy_drinks(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    energy_drinks = db.query(EnergyDrink).offset(skip).limit(limit).all()
    return energy_drinks

@app.get("/energy_drinks/{energy_drink_id}", response_model=EnergyDrinkResponse)
def read_energy_drink(energy_drink_id: int, db: Session = Depends(get_db)):
    energy_drink = db.query(EnergyDrink).filter(EnergyDrink.id == energy_drink_id).first()
    if energy_drink is None:
        raise HTTPException(status_code=404, detail="Energy drink not found")
    return energy_drink

@app.post("/energy_drinks/", response_model=EnergyDrinkResponse)
def create_energy_drink(energy_drink: EnergyDrinkCreate, db: Session = Depends(get_db)):
    db_energy_drink = EnergyDrink(**energy_drink.dict())
    db.add(db_energy_drink)
    db.commit()
    db.refresh(db_energy_drink)
    return db_energy_drink

@app.put("/energy_drinks/{energy_drink_id}", response_model=EnergyDrinkResponse)
def update_energy_drink(energy_drink_id: int, energy_drink: EnergyDrinkUpdate, db: Session = Depends(get_db)):
    db_energy_drink = db.query(EnergyDrink).filter(EnergyDrink.id == energy_drink_id).first()
    if db_energy_drink is None:
        raise HTTPException(status_code=404, detail="Energy drink not found")
    
    for key, value in energy_drink.dict(exclude_unset=True).items():
        setattr(db_energy_drink, key, value)
    
    db.commit()
    db.refresh(db_energy_drink)
    return db_energy_drink

@app.delete("/energy_drinks/{energy_drink_id}", status_code=204)
def delete_energy_drink(energy_drink_id: int, db: Session = Depends(get_db)):
    db_energy_drink = db.query(EnergyDrink).filter(EnergyDrink.id == energy_drink_id).first()
    if db_energy_drink is None:
        raise HTTPException(status_code=404, detail="Energy drink not found")
    db.delete(db_energy_drink)
    db.commit()
    return None
