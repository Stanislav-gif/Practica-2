from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List

# Создание базы данных и модели
DATABASE_URL = "sqlite:///./mobile_phones.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MobilePhone(Base):
    __tablename__ = "mobile_phones"
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, index=True)
    model = Column(String, index=True)
    price = Column(Float)

Base.metadata.create_all(bind=engine)

# Модели Pydantic для валидации
class MobilePhoneCreate(BaseModel):
    brand: str
    model: str
    price: float

class MobilePhoneUpdate(BaseModel):
    brand: str = None
    model: str = None
    price: float = None

class MobilePhoneResponse(BaseModel):
    id: int
    brand: str
    model: str
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

@app.get("/mobile_phones/", response_model=List[MobilePhoneResponse])
def read_mobile_phones(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    mobile_phones = db.query(MobilePhone).offset(skip).limit(limit).all()
    return mobile_phones

@app.get("/mobile_phones/{mobile_phone_id}", response_model=MobilePhoneResponse)
def read_mobile_phone(mobile_phone_id: int, db: Session = Depends(get_db)):
    mobile_phone = db.query(MobilePhone).filter(MobilePhone.id == mobile_phone_id).first()
    if mobile_phone is None:
        raise HTTPException(status_code=404, detail="Mobile phone not found")
    return mobile_phone

@app.post("/mobile_phones/", response_model=MobilePhoneResponse)
def create_mobile_phone(mobile_phone: MobilePhoneCreate, db: Session = Depends(get_db)):
    db_mobile_phone = MobilePhone(**mobile_phone.dict())
    db.add(db_mobile_phone)
    db.commit()
    db.refresh(db_mobile_phone)
    return db_mobile_phone

@app.put("/mobile_phones/{mobile_phone_id}", response_model=MobilePhoneResponse)
def update_mobile_phone(mobile_phone_id: int, mobile_phone: MobilePhoneUpdate, db: Session = Depends(get_db)):
    db_mobile_phone = db.query(MobilePhone).filter(MobilePhone.id == mobile_phone_id).first()
    if db_mobile_phone is None:
        raise HTTPException(status_code=404, detail="Mobile phone not found")
    
    for key, value in mobile_phone.dict(exclude_unset=True).items():
        setattr(db_mobile_phone, key, value)
    
    db.commit()
    db.refresh(db_mobile_phone)
    return db_mobile_phone

@app.delete("/mobile_phones/{mobile_phone_id}", status_code=204)
def delete_mobile_phone(mobile_phone_id: int, db: Session = Depends(get_db)):
    db_mobile_phone = db.query(MobilePhone).filter(MobilePhone.id == mobile_phone_id).first()
    if db_mobile_phone is None:
        raise HTTPException(status_code=404, detail="Mobile phone not found")
    db.delete(db_mobile_phone)
    db.commit()
    return None
