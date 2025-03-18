from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, constr
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Literal

# Создание базы данных и модели
DATABASE_URL = "sqlite:///./computer_parts.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Определение допустимых типов компонентов
ComputerPartType = Literal[
    "Процессор",
    "Видеокарта",
    "Материнская плата",
    "Оперативная память",
    "Накопитель",
    "Блок питания",
    "Корпус",
    "Система охлаждения"
]

class ComputerPart(Base):
    __tablename__ = "computer_parts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    part_type = Column(String)  # Тип компонента (например, процессор, видеокарта и т.д.)

Base.metadata.create_all(bind=engine)

# Модели Pydantic для валидации
class ComputerPartCreate(BaseModel):
    name: str
    price: float
    part_type: ComputerPartType 

class ComputerPartUpdate(BaseModel):
    name: str = None
    price: float = None
    part_type: ComputerPartType = None  

class ComputerPartResponse(BaseModel):
    id: int
    name: str
    price: float
    part_type: ComputerPartType 

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

@app.get("/computer_parts/", response_model=List[ComputerPartResponse])
def read_computer_parts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    computer_parts = db.query(ComputerPart).offset(skip).limit(limit).all()
    return computer_parts

@app.get("/computer_parts/{part_id}", response_model=ComputerPartResponse)
def read_computer_part(part_id: int, db: Session = Depends(get_db)):
    computer_part = db.query(ComputerPart).filter(ComputerPart.id == part_id).first()
    if computer_part is None:
        raise HTTPException(status_code=404, detail="Computer part not found")
    return computer_part

@app.post("/computer_parts/", response_model=ComputerPartResponse)
def create_computer_part(computer_part: ComputerPartCreate, db: Session = Depends(get_db)):
    db_computer_part = ComputerPart(**computer_part.dict())
    db.add(db_computer_part)
    db.commit()
    db.refresh(db_computer_part)
    return db_computer_part

@app.put("/computer_parts/{part_id}", response_model=ComputerPartResponse)
def update_computer_part(part_id: int, computer_part: ComputerPartUpdate, db: Session = Depends(get_db)):
    db_computer_part = db.query(ComputerPart).filter(ComputerPart.id == part_id).first()
    if db_computer_part is None:
        raise HTTPException(status_code=404, detail="Computer part not found")
    
    for key, value in computer_part.dict(exclude_unset=True).items():
        setattr(db_computer_part, key, value)
    
    db.commit()
    db.refresh(db_computer_part)
    return db_computer_part

@app.delete("/computer_parts/{part_id}", status_code=204)
def delete_computer_part(part_id: int, db: Session = Depends(get_db)):
    db_computer_part = db.query(ComputerPart).filter(ComputerPart.id == part_id).first()
    if db_computer_part is None:
        raise HTTPException(status_code=404, detail="Computer part not found")
    db.delete(db_computer_part)
    db.commit()
    return None
