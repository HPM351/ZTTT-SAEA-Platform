import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from database import SessionLocal, User, ChatSession, ChatMessage

history_router = APIRouter(prefix="/api/chat", tags=["Chat History"])
security = HTTPBearer()

# 这里的密钥必须和 api_auth.py 里签发 Token 时用的一模一样
SECRET_KEY = "ZTTT_SAEA_SUPER_SECRET_KEY_FOR_MICROWAVE_LAB"
ALGORITHM = "HS256"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 核心安全守卫：解析 JWT Token，找出当前操作的用户
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token 无效")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="登录已过期或无效，请重新登录")


# ================= Pydantic 数据模型 =================
class MessageItem(BaseModel):
    role: str
    content: str


class SyncSessionRequest(BaseModel):
    id: str
    title: str
    messages: List[MessageItem]


# ================= 业务接口 =================

@history_router.get("/history")
def get_my_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前登录用户的所有历史对话记录"""
    # 按照更新时间倒序，最近聊过的排在最前面
    sessions = db.query(ChatSession).filter(ChatSession.owner_id == current_user.id).order_by(
        ChatSession.updated_at.desc()).all()

    result = []
    for s in sessions:
        # 按 ID 升序保证消息顺序正确
        msgs = db.query(ChatMessage).filter(ChatMessage.session_id == s.id).order_by(ChatMessage.id.asc()).all()
        result.append({
            "id": s.id,
            "title": s.title,
            "timestamp": int(s.updated_at.timestamp() * 1000),
            "messages": [{"role": m.role, "content": m.content} for m in msgs]
        })
    return {"status": "success", "data": result}


@history_router.post("/sync")
def sync_chat_session(req: SyncSessionRequest, current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """同步（覆盖保存）某一次对话的所有消息"""
    session = db.query(ChatSession).filter(ChatSession.id == req.id).first()

    if not session:
        # 如果会话不存在，新建它
        session = ChatSession(id=req.id, title=req.title, owner_id=current_user.id)
        db.add(session)
    else:
        # 权限校验：不能修改别人的会话
        if session.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权修改此会话")
        # 更新标题（处理用户重命名的情况）
        session.title = req.title

    # 同步策略：为了应对流式输出带来的频繁更新，直接清空旧消息并全量写入新消息
    db.query(ChatMessage).filter(ChatMessage.session_id == req.id).delete()

    for msg in req.messages:
        db.add(ChatMessage(session_id=req.id, role=msg.role, content=msg.content))

    db.commit()
    return {"status": "success"}


@history_router.delete("/session/{session_id}")
def delete_chat_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """删除某次对话记录"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id,
                                           ChatSession.owner_id == current_user.id).first()
    if session:
        db.delete(session)  # 借助 SQLAlchemy 的 cascade 级联机制，底下的 messages 会被自动删除
        db.commit()
    return {"status": "success"}