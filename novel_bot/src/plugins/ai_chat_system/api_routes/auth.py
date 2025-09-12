# novel_bot/src/plugins/ai_chat_system/api_routes/auth.py

from fastapi import APIRouter, Body, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from ..services.user_service import UserService, get_user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterPayload(BaseModel):
    username: str
    password: str
    account_digits: int = 8
    security_questions: List[Dict[str, str]] = Field(..., min_length=3, max_length=3)
    anonymous_user_id: str

class LoginPayload(BaseModel):
    username_or_account: str
    password: str

class ForgotPasswordRequestPayload(BaseModel):
    account_number: str

class ResetPasswordPayload(BaseModel):
    account_number: str
    answers: List[str] = Field(..., min_length=3, max_length=3)
    new_password: str

# [核心新增] 注销账号载荷
class DeleteAccountPayload(BaseModel):
    user_id: str
    password: str

@router.post("/register")
async def register_user(
    payload: RegisterPayload,
    service: UserService = Depends(get_user_service)
):
    try:
        user_info = await service.create_user(
            username=payload.username, password=payload.password,
            account_digits=payload.account_digits, security_questions=payload.security_questions,
            anonymous_user_id=payload.anonymous_user_id
        )
        return {"status": "success", "message": "注册成功！", "user_info": user_info}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {e}")

@router.post("/login")
async def login_user(
    payload: LoginPayload,
    service: UserService = Depends(get_user_service)
):
    user = await service.authenticate_user(payload.username_or_account, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名/账号或密码不正确，请检查后重试。")
    return {
        "status": "success", "message": "登录成功！", 
        "user_info": {
            "user_id": user["user_id"], "username": user["username"],
            "account_number": user["account_number"], "avatar": user.get("avatar")
        }
    }

@router.post("/delete-account")
async def delete_account(
    payload: DeleteAccountPayload,
    service: UserService = Depends(get_user_service)
):
    success = await service.delete_user(payload.user_id, payload.password)
    if not success:
        raise HTTPException(status_code=401, detail="密码不正确或用户不存在，无法注销账号。")
    return {"status": "success", "message": "账号已成功注销。"}

@router.post("/forgot-password/questions")
async def get_security_questions(
    payload: ForgotPasswordRequestPayload,
    service: UserService = Depends(get_user_service)
):
    questions = await service.get_user_security_questions(payload.account_number)
    if not questions:
        raise HTTPException(status_code=404, detail="账号不存在或未设置安全问题。")
    return {"status": "success", "questions": questions}

@router.post("/forgot-password/reset")
async def reset_password(
    payload: ResetPasswordPayload,
    service: UserService = Depends(get_user_service)
):
    success = await service.reset_password_with_answers(
        payload.account_number, payload.answers, payload.new_password
    )
    if not success:
        raise HTTPException(status_code=400, detail="安全问题答案不正确或操作失败。")
    return {"status": "success", "message": "密码重置成功！您现在可以用新密码登录。"}