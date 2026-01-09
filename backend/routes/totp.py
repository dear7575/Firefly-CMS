"""
两步验证 (2FA/TOTP) 相关路由
提供 TOTP 设置、验证、禁用和恢复码管理功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
import pyotp
import qrcode
import io
import base64
import secrets
import json

from database import get_db
from routes.auth import get_current_user
from auth import get_password_hash, verify_password
import models

router = APIRouter(prefix="/totp", tags=["两步验证"])


# ============ 请求/响应模型 ============

class TOTPSetupResponse(BaseModel):
    """2FA 设置响应"""
    secret: str
    qr_code: str  # Base64 编码的 PNG 图片
    manual_entry_key: str
    issuer: str


class TOTPVerifyRequest(BaseModel):
    """验证 TOTP 请求"""
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class TOTPDisableRequest(BaseModel):
    """禁用 2FA 请求"""
    password: str = Field(..., min_length=1)
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class RecoveryCodeVerifyRequest(BaseModel):
    """恢复码验证请求"""
    code: str = Field(..., min_length=6, max_length=10)


# ============ 工具函数 ============

def generate_recovery_codes(count: int = 10) -> list[str]:
    """
    生成恢复码（10个8位随机码）

    Args:
        count: 生成的恢复码数量，默认10个

    Returns:
        list[str]: 恢复码列表，格式如 "ABCD1234"
    """
    return [secrets.token_hex(4).upper() for _ in range(count)]


def generate_qr_code(uri: str) -> str:
    """
    生成二维码并返回 Base64 编码

    Args:
        uri: TOTP otpauth:// URI

    Returns:
        str: Base64 编码的 PNG 图片数据
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode()


def hash_recovery_codes(codes: list[str]) -> list[str]:
    """
    对恢复码进行哈希处理

    Args:
        codes: 原始恢复码列表

    Returns:
        list[str]: 哈希后的恢复码列表
    """
    return [get_password_hash(code) for code in codes]


def verify_recovery_code_from_list(code: str, hashed_codes: list[str]) -> int:
    """
    验证恢复码是否有效

    Args:
        code: 用户输入的恢复码
        hashed_codes: 存储的哈希恢复码列表

    Returns:
        int: 匹配的索引，-1 表示未找到
    """
    code_normalized = code.upper().replace("-", "").replace(" ", "")
    for i, hashed in enumerate(hashed_codes):
        if verify_password(code_normalized, hashed):
            return i
    return -1


# ============ API 端点 ============

@router.get("/status", summary="获取2FA状态")
async def get_totp_status(
    current_user: models.Admin = Depends(get_current_user)
):
    """
    获取当前用户的2FA启用状态

    返回：
    - enabled: 是否启用
    - verified: 是否已验证
    - enabled_at: 启用时间
    - recovery_codes_count: 剩余恢复码数量
    """
    recovery_count = 0
    if current_user.recovery_codes:
        try:
            codes = json.loads(current_user.recovery_codes)
            recovery_count = len(codes)
        except:
            pass

    return {
        "enabled": current_user.totp_enabled,
        "verified": current_user.totp_verified,
        "enabled_at": current_user.totp_enabled_at.isoformat() if current_user.totp_enabled_at else None,
        "recovery_codes_count": recovery_count
    }


@router.post("/setup", response_model=TOTPSetupResponse, summary="生成2FA设置")
async def setup_totp(
    current_user: models.Admin = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成 TOTP 密钥和二维码

    返回二维码供用户扫描，需要调用 /verify 确认设置。

    注意：如果 2FA 已启用，需要先调用 /disable 禁用后才能重新设置。
    """
    if current_user.totp_enabled and current_user.totp_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA 已启用，请先禁用后再重新设置"
        )

    # 生成新的 TOTP 密钥（32字符 Base32 编码）
    secret = pyotp.random_base32()
    issuer = "Firefly CMS"

    # 生成 otpauth URI
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=current_user.username,
        issuer_name=issuer
    )

    # 生成二维码
    qr_base64 = generate_qr_code(uri)

    # 保存密钥（未验证状态）
    current_user.totp_secret = secret
    current_user.totp_verified = False
    db.commit()

    return TOTPSetupResponse(
        secret=secret,
        qr_code=f"data:image/png;base64,{qr_base64}",
        manual_entry_key=secret,
        issuer=issuer
    )


@router.post("/verify", summary="验证并启用2FA")
async def verify_totp(
    request: TOTPVerifyRequest,
    current_user: models.Admin = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    验证 TOTP 码并正式启用 2FA

    用户扫描二维码后，输入验证器 App 显示的6位验证码完成设置。

    成功后返回恢复码，请妥善保存！恢复码只显示一次。
    """
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先调用 /setup 生成密钥"
        )

    if current_user.totp_enabled and current_user.totp_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA 已启用"
        )

    # 验证 TOTP 码（允许前后30秒的偏差）
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(request.code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误，请检查手机时间是否准确"
        )

    # 生成恢复码
    recovery_codes = generate_recovery_codes(10)
    hashed_codes = hash_recovery_codes(recovery_codes)

    # 启用 2FA
    current_user.totp_enabled = True
    current_user.totp_verified = True
    current_user.totp_enabled_at = datetime.utcnow()
    current_user.recovery_codes = json.dumps(hashed_codes)
    current_user.last_totp_used = None
    db.commit()

    return {
        "message": "2FA 已成功启用",
        "recovery_codes": recovery_codes,
        "warning": "请妥善保存这些恢复码，它们只会显示一次！如果丢失手机，可以使用恢复码登录。"
    }


@router.post("/disable", summary="禁用2FA")
async def disable_totp(
    request: TOTPDisableRequest,
    current_user: models.Admin = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    禁用 2FA

    需要同时提供：
    - 当前账户密码
    - 验证器 App 中的6位验证码

    禁用后所有 2FA 设置将被清除。
    """
    if not current_user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA 未启用"
        )

    # 验证密码
    if not verify_password(request.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码错误"
        )

    # 验证 TOTP
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(request.code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误"
        )

    # 清除 2FA 设置
    current_user.totp_secret = None
    current_user.totp_enabled = False
    current_user.totp_verified = False
    current_user.recovery_codes = None
    current_user.totp_enabled_at = None
    current_user.last_totp_used = None
    db.commit()

    return {"message": "2FA 已禁用"}


@router.post("/regenerate-recovery", summary="重新生成恢复码")
async def regenerate_recovery_codes(
    request: TOTPVerifyRequest,
    current_user: models.Admin = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    重新生成恢复码

    需要提供当前验证器 App 中的6位验证码。

    生成后，旧的恢复码将全部失效。
    """
    if not current_user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA 未启用"
        )

    # 验证 TOTP
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(request.code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误"
        )

    # 生成新恢复码
    recovery_codes = generate_recovery_codes(10)
    hashed_codes = hash_recovery_codes(recovery_codes)
    current_user.recovery_codes = json.dumps(hashed_codes)
    db.commit()

    return {
        "message": "恢复码已重新生成",
        "recovery_codes": recovery_codes,
        "warning": "旧恢复码已全部失效，请妥善保存新的恢复码！"
    }


@router.get("/recovery-count", summary="获取剩余恢复码数量")
async def get_recovery_codes_count(
    current_user: models.Admin = Depends(get_current_user)
):
    """
    获取剩余可用恢复码的数量
    """
    if not current_user.totp_enabled:
        return {"count": 0}

    if not current_user.recovery_codes:
        return {"count": 0}

    try:
        codes = json.loads(current_user.recovery_codes)
        return {"count": len(codes)}
    except:
        return {"count": 0}
