import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from app.db import get_conn
from app.schemas.auth import UserRegister, UserResponse


def hash_password(password: str, salt: Optional[str] = None) -> tuple:
    """密码加密"""
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return pwd_hash, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """验证密码"""
    pwd_hash, _ = hash_password(password, salt)
    return pwd_hash == stored_hash


def register_user(user_data: UserRegister) -> UserResponse:
    """注册新用户"""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM zhinote_users WHERE username = %s", (user_data.username,))
        if cursor.fetchone():
            raise ValueError("用户名已存在")
        
        # 检查邮箱是否已存在
        if user_data.email:
            cursor.execute("SELECT id FROM zhinote_users WHERE email = %s", (user_data.email,))
            if cursor.fetchone():
                raise ValueError("邮箱已被注册")
        
        # 检查手机号是否已存在
        if user_data.phone:
            cursor.execute("SELECT id FROM zhinote_users WHERE phone = %s", (user_data.phone,))
            if cursor.fetchone():
                raise ValueError("手机号已被注册")
        
        # 加密密码
        pwd_hash, salt = hash_password(user_data.password)
        password_with_salt = f"{salt}${pwd_hash}"
        
        # 插入新用户
        cursor.execute(
            """
            INSERT INTO zhinote_users (username, nickname, email, phone, password_hash)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_data.username, user_data.username, user_data.email, user_data.phone, password_with_salt)
        )
        user_id = cursor.lastrowid
        conn.commit()
        
        # 获取用户信息
        cursor.execute(
            """
            SELECT id, username, nickname, email, phone, avatar_url, created_at, last_login
            FROM zhinote_users WHERE id = %s
            """,
            (user_id,)
        )
        user = cursor.fetchone()
        
        return UserResponse(
            id=user[0],
            username=user[1],
            nickname=user[2],
            email=user[3],
            phone=user[4],
            avatar_url=user[5],
            created_at=user[6],
            last_login=user[7]
        )
    finally:
        cursor.close()
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """用户认证"""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 查找用户
        cursor.execute(
            """
            SELECT id, username, nickname, email, phone, password_hash, avatar_url, created_at, last_login, is_active
            FROM zhinote_users WHERE username = %s
            """,
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            return None
        
        if not user[9]:  # is_active
            return None
        
        # 验证密码
        salt, stored_hash = user[5].split('$', 1)
        if not verify_password(password, stored_hash, salt):
            return None
        
        # 更新最后登录时间
        cursor.execute(
            "UPDATE zhinote_users SET last_login = %s WHERE id = %s",
            (datetime.now(), user[0])
        )
        conn.commit()
        
        return {
            "id": user[0],
            "username": user[1],
            "nickname": user[2],
            "email": user[3],
            "phone": user[4],
            "avatar_url": user[6],
            "created_at": user[7],
            "last_login": user[8]
        }
    finally:
        cursor.close()
        conn.close()


def get_user_by_id(user_id: int) -> Optional[UserResponse]:
    """根据ID获取用户信息"""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT id, username, nickname, email, phone, avatar_url, created_at, last_login
            FROM zhinote_users WHERE id = %s
            """,
            (user_id,)
        )
        user = cursor.fetchone()
        
        if not user:
            return None
        
        return UserResponse(
            id=user[0],
            username=user[1],
            nickname=user[2],
            email=user[3],
            phone=user[4],
            avatar_url=user[5],
            created_at=user[6],
            last_login=user[7]
        )
    finally:
        cursor.close()
        conn.close()


def create_password_reset_token(user_id: int) -> str:
    """创建密码重置令牌"""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 生成令牌
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)
        
        # 删除旧的未使用令牌
        cursor.execute(
            "DELETE FROM zhinote_password_reset_tokens WHERE user_id = %s AND used = 0",
            (user_id,)
        )
        
        # 插入新令牌
        cursor.execute(
            """
            INSERT INTO zhinote_password_reset_tokens (user_id, token, expires_at)
            VALUES (%s, %s, %s)
            """,
            (user_id, token, expires_at)
        )
        conn.commit()
        
        return token
    finally:
        cursor.close()
        conn.close()


def verify_reset_token(token: str) -> Optional[int]:
    """验证密码重置令牌"""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT user_id, expires_at, used
            FROM zhinote_password_reset_tokens
            WHERE token = %s
            """,
            (token,)
        )
        result = cursor.fetchone()
        
        if not result:
            return None
        
        user_id, expires_at, used = result
        
        if used:
            return None
        
        if datetime.now() > expires_at:
            return None
        
        return user_id
    finally:
        cursor.close()
        conn.close()


def reset_password(token: str, new_password: str) -> bool:
    """重置密码"""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 验证令牌
        user_id = verify_reset_token(token)
        if not user_id:
            return False
        
        # 加密新密码
        pwd_hash, salt = hash_password(new_password)
        password_with_salt = f"{salt}${pwd_hash}"
        
        # 更新密码
        cursor.execute(
            "UPDATE zhinote_users SET password_hash = %s WHERE id = %s",
            (password_with_salt, user_id)
        )
        
        # 标记令牌为已使用
        cursor.execute(
            "UPDATE zhinote_password_reset_tokens SET used = 1 WHERE token = %s",
            (token,)
        )
        
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()


def update_user_profile(user_id: int, nickname: str = None, email: str = None, phone: str = None, avatar_url: str = None) -> Optional[UserResponse]:
    """更新用户资料"""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 构建更新语句
        update_fields = []
        update_values = []
        
        if nickname is not None:
            update_fields.append("nickname = %s")
            update_values.append(nickname)
        
        if email is not None:
            # 检查邮箱是否已被其他用户使用
            cursor.execute("SELECT id FROM zhinote_users WHERE email = %s AND id != %s", (email, user_id))
            if cursor.fetchone():
                raise ValueError("邮箱已被其他用户使用")
            update_fields.append("email = %s")
            update_values.append(email)
        
        if phone is not None:
            # 检查手机号是否已被其他用户使用
            cursor.execute("SELECT id FROM zhinote_users WHERE phone = %s AND id != %s", (phone, user_id))
            if cursor.fetchone():
                raise ValueError("手机号已被其他用户使用")
            update_fields.append("phone = %s")
            update_values.append(phone)
        
        if avatar_url is not None:
            update_fields.append("avatar_url = %s")
            update_values.append(avatar_url)
        
        if not update_fields:
            # 没有需要更新的字段
            return get_user_by_id(user_id)
        
        # 执行更新
        update_values.append(user_id)
        sql = f"UPDATE zhinote_users SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(sql, update_values)
        conn.commit()
        
        # 返回更新后的用户信息
        return get_user_by_id(user_id)
    finally:
        cursor.close()
        conn.close()
