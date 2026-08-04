from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import timedelta

from .database.session import get_db
from .database.models import User
from .auth import get_password_hash, verify_password, create_access_token, get_current_user, validate_password, limiter, ACCESS_TOKEN_EXPIRE_MINUTES
from .schemas import RegisterRequest, LoginRequest, LoginResponse, ActivateLicenseRequest, UserProfileResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Limite stricte sur l'inscription/connexion — le limiteur par défaut
# (60/minute, main.py) protège l'API en général, mais laissait login/register
# sans frein spécifique contre le bruteforce/credential stuffing.
@router.post("/register")
@limiter.limit("5/minute")
def register(request: Request, data: RegisterRequest, db: Session = Depends(get_db)):
    validate_password(data.password)

    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
        
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        role="user",
        is_premium=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "Utilisateur créé avec succès"}

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        is_premium=user.is_premium,
        email=user.email,
    )

@router.post("/activate")
def activate_license(data: ActivateLicenseRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Validation basique pour le mock — sera remplacé par licensing.py (Lot C)
    if data.license_key.startswith("GS-PRO-"):
        current_user.license_key = data.license_key
        current_user.is_premium = True
        db.commit()
        return {"message": "Licence activée avec succès, bienvenue dans GREEN SHIELD PRO !"}
    else:
        raise HTTPException(status_code=400, detail="Clé de licence invalide")

@router.get("/me", response_model=UserProfileResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserProfileResponse(
        email=current_user.email,
        role=current_user.role,
        is_premium=current_user.is_premium,
        license_key=current_user.license_key,
        plan=getattr(current_user, "plan", "free") or "free",
    )
