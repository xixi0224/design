from fastapi import APIRouter, HTTPException
from app.schemas.auth import UserRegister, UserLogin, LoginResponse, PasswordResetRequest, PasswordResetConfirm, UserProfileUpdate, UserResponse
from app.services.auth_service import register_user, authenticate_user, create_password_reset_token, reset_password, update_user_profile

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=LoginResponse)
async def register(user_data: UserRegister):
    """用户注册"""
    try:
        user = register_user(user_data)
        return LoginResponse(
            success=True,
            message="注册成功",
            user=user
        )
    except ValueError as e:
        return LoginResponse(
            success=False,
            message=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@router.post("/login", response_model=LoginResponse)
async def login(login_data: UserLogin):
    """用户登录"""
    try:
        user = authenticate_user(login_data.username, login_data.password)
        
        if not user:
            return LoginResponse(
                success=False,
                message="用户名或密码错误"
            )
        
        # 这里可以生成JWT token，暂时使用简单的token
        token = f"user_{user['id']}_{user['username']}"
        
        from app.schemas.auth import UserResponse
        user_response = UserResponse(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            phone=user['phone'],
            avatar_url=user['avatar_url'],
            created_at=user['created_at'],
            last_login=user['last_login']
        )
        
        return LoginResponse(
            success=True,
            message="登录成功",
            user=user_response,
            token=token
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")


@router.post("/password-reset-request")
async def request_password_reset(request: PasswordResetRequest):
    """请求密码重置"""
    try:
        from app.db import get_conn
        
        conn = get_conn()
        cursor = conn.cursor()
        
        try:
            # 查找用户
            cursor.execute(
                "SELECT id FROM zhinote_users WHERE email = %s",
                (request.email,)
            )
            user = cursor.fetchone()
            
            if not user:
                return {"success": False, "message": "该邮箱未注册"}
            
            # 创建重置令牌
            token = create_password_reset_token(user[0])
            
            # 在实际应用中，这里应该发送邮件
            # 现在我们只返回token（实际应该通过邮件发送）
            return {
                "success": True,
                "message": "密码重置链接已发送到您的邮箱",
                "token": token  # 开发环境返回token，生产环境应该移除
            }
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"密码重置请求失败: {str(e)}")


@router.post("/password-reset-confirm")
async def confirm_password_reset(request: PasswordResetConfirm):
    """确认密码重置"""
    try:
        success = reset_password(request.token, request.new_password)
        
        if success:
            return {"success": True, "message": "密码重置成功"}
        else:
            return {"success": False, "message": "无效的或已过期的重置令牌"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"密码重置失败: {str(e)}")


@router.put("/user/profile/{user_id}", response_model=UserResponse)
async def update_profile(user_id: int, profile_data: UserProfileUpdate):
    """更新用户资料"""
    try:
        user = update_user_profile(
            user_id=user_id,
            nickname=profile_data.nickname,
            email=profile_data.email,
            phone=profile_data.phone,
            avatar_url=profile_data.avatar_url
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新用户资料失败: {str(e)}")
