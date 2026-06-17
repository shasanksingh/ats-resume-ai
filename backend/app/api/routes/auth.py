from fastapi import APIRouter, Header, HTTPException, Response, status

from app.schemas.auth import AuthRequest, AuthResponse, LoginRequest, UserProfile
from app.services.auth import AuthError, create_user, get_user_by_token, login_user, revoke_session

router = APIRouter(prefix="/auth", tags=["Optional Account"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: AuthRequest):
    try:
        return create_user(payload.name, payload.email, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    try:
        return login_user(payload.email, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me", response_model=UserProfile)
def me(x_session_token: str | None = Header(default=None)):
    user = get_user_by_token(x_session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Sign in to view this account.")
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, x_session_token: str | None = Header(default=None)):
    revoke_session(x_session_token)
    response.status_code = status.HTTP_204_NO_CONTENT
