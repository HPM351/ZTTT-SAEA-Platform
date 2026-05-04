import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import bcrypt
from database import SessionLocal, User

auth_router = APIRouter(prefix="/api", tags=["Authentication"])

# JWT 配置
SECRET_KEY = "ZTTT_SAEA_SUPER_SECRET_KEY_FOR_MICROWAVE_LAB"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30  # 颁发 30 天超长有效期的 Token


class LoginRequest(BaseModel):
    username: str
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 原生 bcrypt 校验（需要转为 bytes 进行比对）
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    # 原生 bcrypt 加密
    salt = bcrypt.gensalt()
    pwd_bytes = password.encode('utf-8')
    # 存入数据库时解码回普通字符串
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@auth_router.post("/register")
async def register(req: LoginRequest, db: Session = Depends(get_db)):
    """明确的注册接口"""
    if not req.username or not req.password:
        return {"status": "error", "message": "账号或密码不能为空"}

    # 检查是否已被注册
    user = db.query(User).filter(User.username == req.username).first()
    if user:
        return {"status": "error", "message": "该账号已被注册，请直接登录"}

    # 创建新账号
    hashed_password = get_password_hash(req.password)
    new_user = User(username=req.username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 注册成功后，直接为其签发 Token，实现“注册即登录”的丝滑体验
    access_token = create_access_token(data={"sub": new_user.username})
    return {
        "status": "success",
        "message": f"注册成功！欢迎加入，{new_user.username}",
        "token": access_token
    }


@auth_router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """明确的登录接口"""
    if not req.username or not req.password:
        return {"status": "error", "message": "账号或密码不能为空"}

    user = db.query(User).filter(User.username == req.username).first()

    # 严格拦截未知账号
    if not user:
        return {"status": "error", "message": "账号不存在，请先检查学号或点击注册"}

    # 严格比对密码
    if not verify_password(req.password, user.password_hash):
        return {"status": "error", "message": "密码错误，请重试！"}

    access_token = create_access_token(data={"sub": user.username})
    return {
        "status": "success",
        "message": f"欢迎回来，{user.username}",
        "token": access_token
    }