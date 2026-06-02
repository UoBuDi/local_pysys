"""
云门户系统路由模块 — 转发代理
所有请求转发至 GUI 服务 (172.32.48.239:9000)，由 GUI 服务处理与云门户的通信。
包括：
- 验证码获取与OCR识别
- SSO 登录与自动登录
- 会话状态管理
- AI稽核数据查询
- 图片获取与代理
- 工单详情查询
- 云门户账号管理
"""

import logging
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime

import requests as http_requests
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.config import get_config as get_app_config

logger = logging.getLogger(__name__)

router = APIRouter()

GUI_SERVICE_BASE = "http://172.32.48.239:9000"

_gui_session = http_requests.Session()
_gui_session.trust_env = False
_gui_session.headers.update({
    "Content-Type": "application/json",
    "Accept": "application/json",
})

from captcha_ocr import recognize_captcha, is_ocr_available as _local_ocr_available_func


def _local_ocr_classify(img_base64: str) -> Optional[str]:
    success, text, msg = recognize_captcha(img_base64, preprocess=True)
    if success:
        return text
    logger.warning(f"本地 OCR 识别失败: {msg}")
    return None


def _forward_get(path: str, params: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
    url = f"{GUI_SERVICE_BASE}{path}"
    try:
        resp = _gui_session.get(url, params=params, timeout=timeout)

        if not resp.text:
            logger.error(f"GUI返回空响应: {url} status={resp.status_code}")
            raise HTTPException(
                status_code=502,
                detail=f"GUI服务返回空响应 (status={resp.status_code})"
            )

        if resp.status_code == 401:
            logger.warning(f"GUI会话过期: {url}")
            raise HTTPException(
                status_code=502,
                detail="云门户会话已过期或无效，请重新登录"
            )
        if resp.status_code >= 400:
            logger.error(f"GUI返回错误: {url} status={resp.status_code} body={resp.text[:500]}")
            raise HTTPException(
                status_code=502,
                detail=f"GUI服务返回错误 (status={resp.status_code})"
            )

        return resp.json()
    except http_requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="GUI服务响应超时")
    except http_requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="无法连接GUI服务")
    except ValueError as e:
        logger.error(f"GUI返回非JSON响应: {url} body={resp.text[:500] if 'resp' in dir() else 'N/A'}")
        raise HTTPException(
            status_code=502,
            detail=f"GUI服务返回非JSON响应: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"转发请求异常: {url} error={e}")
        raise HTTPException(status_code=500, detail=f"转发请求失败: {str(e)}")


def _forward_post(path: str, data: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
    url = f"{GUI_SERVICE_BASE}{path}"
    try:
        resp = _gui_session.post(url, json=data, timeout=timeout)

        if not resp.text:
            logger.error(f"GUI返回空响应: {url} status={resp.status_code}")
            raise HTTPException(
                status_code=502,
                detail=f"GUI服务返回空响应 (status={resp.status_code})"
            )

        if resp.status_code == 401:
            logger.warning(f"GUI会话过期: {url}")
            raise HTTPException(
                status_code=502,
                detail="云门户会话已过期或无效，请重新登录"
            )
        if resp.status_code >= 400:
            logger.error(f"GUI返回错误: {url} status={resp.status_code} body={resp.text[:500]}")
            raise HTTPException(
                status_code=502,
                detail=f"GUI服务返回错误 (status={resp.status_code})"
            )

        return resp.json()
    except http_requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="GUI服务响应超时")
    except http_requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="无法连接GUI服务")
    except ValueError as e:
        logger.error(f"GUI返回非JSON响应: {url} body={resp.text[:500] if 'resp' in dir() else 'N/A'}")
        raise HTTPException(
            status_code=502,
            detail=f"GUI服务返回非JSON响应: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"转发请求异常: {url} error={e}")
        raise HTTPException(status_code=500, detail=f"转发请求失败: {str(e)}")


# ==================== 请求模型 ====================


class LoginRequest(BaseModel):
    uuid: str
    username: str
    password: str
    captcha: str


class AutoLoginRequest(BaseModel):
    username: str
    password: str


class QueryRequest(BaseModel):
    query_params: Dict[str, Any]


class LogoutRequest(BaseModel):
    pass


class AIBatchQueryRequest(BaseModel):
    plate_number: str
    entry_time: str
    gate_time: str
    pass_id: Optional[str] = None
    hours: Optional[int] = 5
    rows: Optional[int] = 20


class VehicleImagesRequest(BaseModel):
    plate_number: str
    start_time: str
    end_time: str
    page: Optional[int] = 0
    page_size: Optional[int] = 20
    sort: Optional[str] = "picTime DESC"


class GantryImagesRequest(BaseModel):
    station_id: str
    start_time: str
    end_time: str
    rows: Optional[int] = 20
    start: Optional[int] = 0
    sort: Optional[str] = "picTime DESC"


class GantryTradeRequest(BaseModel):
    query_value: str
    start_time: str
    end_time: str


class GantryPlateRequest(BaseModel):
    plate_number: str
    start_time: str
    end_time: str


class ExitTradeRequest(BaseModel):
    query_value: str
    start_time: str
    end_time: str
    trade_type: Optional[int] = 1


class SuspectedCarRequest(BaseModel):
    vehicle_or_pass_id: str
    start_time: str
    end_time: str


class AuditOrderRequest(BaseModel):
    vehicle_no: str


class SelectImagesRequest(BaseModel):
    images: List[Dict[str, Any]]
    gantry_ids: List[str]


class OriginalImageRequest(BaseModel):
    picture_path: str


class SaveImagesRequest(BaseModel):
    table_name: str
    record_id: str
    image1_base64: Optional[str] = None
    image2_base64: Optional[str] = None
    review_status: Optional[str] = None
    check_pass_id: Optional[str] = None
    special_situation: Optional[str] = None
    check_split: Optional[str] = None
    remark: Optional[str] = None
    clear_empty: Optional[bool] = None


class FetchPictureRequest(BaseModel):
    picture_url: str


class OCRRequest(BaseModel):
    image: str


class KeepAliveRequest(BaseModel):
    pass


class AccountSaveRequest(BaseModel):
    portal_username: str
    portal_password: str


# ==================== 云门户账号存储（MySQL system_db.portal_accounts） ====================


def _get_mysql_conn():
    config = get_app_config()
    from database import get_db_connection
    return get_db_connection("USER_DB", config)


def _save_account(user_id: int, username: str, password: str):
    with _get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM portal_accounts WHERE user_id = %s", (user_id,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE portal_accounts SET portal_username=%s, portal_password=%s, updated_at=NOW() WHERE user_id=%s",
                    (username, password, user_id),
                )
            else:
                cursor.execute(
                    "INSERT INTO portal_accounts (user_id, portal_username, portal_password, created_at, updated_at) VALUES (%s, %s, %s, NOW(), NOW())",
                    (user_id, username, password),
                )
            conn.commit()


def _get_account(user_id: int) -> Optional[Dict[str, Any]]:
    with _get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM portal_accounts WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))


def _delete_account(user_id: int):
    with _get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM portal_accounts WHERE user_id = %s", (user_id,))
            conn.commit()


def _update_account_tokens(
    user_id: int,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    token_expires_at: Optional[float] = None
):
    with _get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            update_fields = []
            update_values = []

            if access_token is not None:
                update_fields.append("access_token=%s")
                update_values.append(access_token)

            if refresh_token is not None:
                update_fields.append("refresh_token=%s")
                update_values.append(refresh_token)

            if redirect_uri is not None:
                update_fields.append("redirect_uri=%s")
                update_values.append(redirect_uri)

            if token_expires_at is not None:
                update_fields.append("token_expires_at=%s")
                update_values.append(token_expires_at)

            update_fields.append("updated_at=NOW()")
            update_values.append(user_id)

            cursor.execute(
                f"UPDATE portal_accounts SET {', '.join(update_fields)} WHERE user_id=%s",
                tuple(update_values)
            )
            conn.commit()

            logger.info(f"[Token更新] 用户{user_id}的Token信息已更新")


def _is_token_valid(account: Dict[str, Any]) -> bool:
    """检查Token是否有效"""
    import time

    if not account.get('access_token'):
        return False

    token_expires_at = account.get('token_expires_at')

    if token_expires_at is None:
        return bool(account.get('access_token'))

    return time.time() < token_expires_at


def _get_access_token(user_id: int) -> str:
    account = _get_account(user_id)
    if account and _is_token_valid(account):
        return account.get("access_token", "")
    return ""


def _auto_relogin(user_id: int) -> Dict[str, Any]:
    """
    自动重登录云门户（内部函数）
    使用数据库中保存的账号密码进行自动登录，更新Token
    """
    import base64 as _base64
    import json as _json

    account = _get_account(user_id)
    if not account:
        return {
            "success": False,
            "message": "未找到保存的云门户账号，请先配置账号密码"
        }

    username = account.get("portal_username", "")
    password = account.get("portal_password", "")

    if not username or not password:
        return {
            "success": False,
            "message": "云门户账号或密码为空，请重新配置"
        }

    max_retries = 3

    for attempt in range(max_retries):
        try:
            logger.info(f"[自动重登录] 第{attempt + 1}次尝试...")

            captcha_result = _forward_get("/api/portal/captcha", timeout=30)

            if captcha_result.get("code") != 200:
                logger.warning(f"[自动重登录] 获取验证码失败: {captcha_result.get('message')}")
                continue

            captcha_data = captcha_result.get("data", {})
            img_base64 = captcha_data.get("img", "")
            captcha_uuid = captcha_data.get("uuid", "")

            if not img_base64:
                logger.warning(f"[自动重登录] 验证码图片为空")
                continue

            ocr_text = None
            try:
                ocr_result = _forward_post("/api/portal/captcha/ocr", data={"image": img_base64}, timeout=15)
                if ocr_result.get("code") == 200 and ocr_result.get("data", {}).get("text"):
                    ocr_text = ocr_result["data"]["text"]
            except HTTPException:
                pass

            if not ocr_text:
                logger.info("[自动重登录] GUI OCR不可用，尝试本地识别")
                ocr_text = _local_ocr_classify(img_base64)

            if not ocr_text:
                logger.warning("[自动重登录] OCR识别验证码失败")
                continue

            login_data = {
                "uuid": captcha_uuid,
                "username": username,
                "password": password,
                "captcha": ocr_text,
            }

            login_result = _forward_post("/api/portal/login", data=login_data, timeout=60)

            if login_result.get("code") == 200:
                login_data_result = login_result.get("data", {})

                access_token = login_data_result.get("access_token")
                refresh_token = login_data_result.get("refresh_token")
                redirect_uri = login_data_result.get("redirect_uri")
                token_expires_at = None

                if access_token:
                    try:
                        parts = access_token.split(".")
                        if len(parts) == 3:
                            payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
                            decoded = _base64.urlsafe_b64decode(payload)
                            token_data = _json.loads(decoded)
                            exp = token_data.get("exp")
                            if exp:
                                token_expires_at = float(exp)
                    except Exception as e:
                        logger.warning(f"[Token解析] 解析过期时间失败: {e}")

                _update_account_tokens(
                    user_id=user_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    redirect_uri=redirect_uri,
                    token_expires_at=token_expires_at
                )

                logger.info(f"[自动重登录] ✅ 用户{user_id}登录成功！Token已更新")
                return {
                    "success": True,
                    "message": "自动重登录成功",
                    "data": {
                        "access_token": access_token,
                        "token_expires_at": token_expires_at
                    }
                }

            if login_result.get("code") in (400, 401) and "验证码" in login_result.get("message", ""):
                logger.info(f"[自动重登录] 第{attempt + 1}次: 验证码错误，重试")
                continue

            logger.error(f"[自动重登录] 登录失败: {login_result.get('message')}")
            return {
                "success": False,
                "message": f"登录失败: {login_result.get('message', '未知错误')}"
            }

        except Exception as e:
            logger.error(f"[自动重登录] 第{attempt + 1}次异常: {e}")
            continue

    logger.error("[自动重登录] ❌ 所有重试均失败")
    return {
        "success": False,
        "message": "自动重登录失败，请手动登录云门户"
    }


# ==================== 路由端点 — 转发至 GUI 服务 ====================


@router.get("/api/cloud-portal/captcha")
async def get_captcha():
    """获取云门户验证码 — 转发至 GUI 服务"""
    return _forward_get("/api/portal/captcha", timeout=30)


@router.post("/api/cloud-portal/login")
async def cloud_portal_login(req: LoginRequest):
    """云门户登录 — 转发至 GUI 服务"""
    return _forward_post("/api/portal/login", data=req.model_dump(), timeout=60)


@router.post("/api/cloud-portal/auto-login")
async def cloud_portal_auto_login(req: AutoLoginRequest, user_id: Optional[int] = Query(None)):
    """云门户自动登录 — 通过 GUI 服务 OCR 识别验证码后自动登录"""
    effective_user_id = user_id or 1
    username = req.username
    password = req.password
    max_retries = 5

    for attempt in range(max_retries):
        try:
            captcha_result = _forward_get("/api/portal/captcha", timeout=30)

            if captcha_result.get("code") != 200:
                return captcha_result

            captcha_data = captcha_result.get("data", {})
            img_base64 = captcha_data.get("img", "")
            captcha_uuid = captcha_data.get("uuid", "")

            if not img_base64:
                logger.warning(f"自动登录第{attempt + 1}次: 验证码图片为空")
                continue

            ocr_text = None
            try:
                ocr_result = _forward_post("/api/portal/captcha/ocr", data={"image": img_base64}, timeout=15)
                if ocr_result.get("code") == 200 and ocr_result.get("data", {}).get("text"):
                    ocr_text = ocr_result["data"]["text"]
            except HTTPException:
                pass

            if not ocr_text:
                logger.warning(f"自动登录第{attempt + 1}次: GUI OCR 不可用，尝试本地识别")
                ocr_text = _local_ocr_classify(img_base64)

            if not ocr_text:
                logger.warning(f"自动登录第{attempt + 1}次: OCR识别失败")
                continue

            login_data = {
                "uuid": captcha_uuid,
                "username": username,
                "password": password,
                "captcha": ocr_text,
            }
            login_result = _forward_post("/api/portal/login", data=login_data, timeout=60)

            if login_result.get("code") == 200:
                login_data_result = login_result.get("data", {})
                import base64 as _base64
                import json as _json
                import time as _time

                access_token = login_data_result.get("access_token")
                refresh_token = login_data_result.get("refresh_token")
                redirect_uri = login_data_result.get("redirect_uri")
                token_expires_at = None

                if access_token:
                    try:
                        parts = access_token.split(".")
                        if len(parts) == 3:
                            payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
                            decoded = _base64.urlsafe_b64decode(payload)
                            token_data = _json.loads(decoded)
                            exp = token_data.get("exp")
                            if exp:
                                token_expires_at = float(exp)
                    except Exception as e:
                        logger.warning(f"[Token解析] 解析过期时间失败: {e}")

                _update_account_tokens(
                    user_id=effective_user_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    redirect_uri=redirect_uri,
                    token_expires_at=token_expires_at
                )
                return login_result

            if login_result.get("code") in (400, 401) and "验证码" in login_result.get("message", ""):
                logger.info(f"自动登录第{attempt + 1}次: 验证码错误，重试")
                continue

            return login_result

        except Exception as e:
            logger.error(f"自动登录第{attempt + 1}次异常: {e}")
            continue

    new_captcha = _forward_get("/api/portal/captcha", timeout=30)
    captcha_data = new_captcha.get("data", {})
    return {
        "code": 201,
        "message": "自动登录失败，需要手动输入验证码",
        "data": {
            "img": captcha_data.get("img", ""),
            "uuid": captcha_data.get("uuid", ""),
            "need_captcha": True,
        },
    }


@router.get("/api/cloud-portal/health")
async def check_cloud_portal_health():
    """云门户服务健康检查 — 转发至 GUI 服务"""
    return _forward_get("/api/portal/health", timeout=10)


@router.post("/api/cloud-portal/logout")
async def cloud_portal_logout(req: Optional[LogoutRequest] = Body(default=None), user_id: Optional[int] = Query(None)):
    """云门户登出 — 清除本地Token并通知GUI服务（保证成功）"""
    effective_user_id = user_id or 1

    logger.info(f"[logout] 开始执行登出操作... 用户ID: {effective_user_id}")

    try:
        _update_account_tokens(
            user_id=effective_user_id,
            access_token=None,
            refresh_token=None,
            redirect_uri=None,
            token_expires_at=None
        )
        logger.info("[logout] ✅ 本地Token已清除")
    except Exception as e:
        logger.error(f"[logout] 清除本地Token失败: {e}")

    gui_notified = False
    try:
        gui_result = _forward_post("/api/portal/logout", timeout=10)
        if gui_result and gui_result.get("code") == 200:
            gui_notified = True
            logger.info("[logout] ✅ GUI服务通知成功")
    except HTTPException as e:
        logger.warning(f"[logout] GUI服务通知失败（不影响登出）: {e.detail}")
    except Exception as e:
        logger.warning(f"[logout] GUI服务通知异常（不影响登出）: {e}")

    message = "登出成功"
    if not gui_notified:
        message += "（本地Token已清除，GUI服务通知跳过）"

    logger.info(f"[logout] 🎉 登出完成: {message}")
    return {
        "code": 200,
        "message": message,
        "data": {
            "local_token_cleared": True,
            "gui_service_notified": gui_notified
        }
    }


@router.post("/api/cloud-portal/keep-alive")
async def cloud_portal_keep_alive(req: KeepAliveRequest, user_id: Optional[int] = Query(None)):
    """保持会话活跃 — 从数据库读取Token并转发至GUI服务进行JWT有效性检查"""
    effective_user_id = user_id or 1
    account = _get_account(effective_user_id)
    if not account or not account.get('access_token'):
        return {
            "code": 200,
            "message": "未登录或无有效Token",
            "data": {"valid": False, "reason": "no_token"}
        }

    return _forward_post("/api/portal/keep-alive", data={"access_token": account['access_token']}, timeout=15)


@router.get("/api/cloud-portal/sessions")
async def get_cloud_portal_sessions():
    """获取所有会话 — 转发至 GUI 服务"""
    return _forward_get("/api/portal/sessions", timeout=10)


@router.post("/api/cloud-portal/query")
async def cloud_portal_query(req: QueryRequest, user_id: Optional[int] = Query(None)):
    """云门户通用查询 — 直接转发至 GUI 服务"""
    payload = req.model_dump()
    payload["access_token"] = _get_access_token(user_id or 1)
    return _forward_post("/api/portal/query", data=payload, timeout=60)


@router.post("/api/cloud-portal/ai-audit/vehicle-images")
async def ai_audit_vehicle_images(req: VehicleImagesRequest, user_id: Optional[int] = Query(None)):
    """AI稽核-车辆图库查询 — 直接转发至 GUI 服务"""
    payload = req.model_dump()
    payload["access_token"] = _get_access_token(user_id or 1)
    return _forward_post("/api/portal/ai-audit/vehicle-images", data=payload, timeout=60)


@router.post("/api/cloud-portal/ai-audit/gantry-images")
async def ai_audit_gantry_images(req: GantryImagesRequest, user_id: Optional[int] = Query(None)):
    """AI稽核-门架图库查询 — 直接转发至 GUI 服务"""
    payload = req.model_dump()
    payload["access_token"] = _get_access_token(user_id or 1)
    return _forward_post("/api/portal/ai-audit/gantry-images", data=payload, timeout=60)


@router.post("/api/cloud-portal/ai-audit/batch-query")
async def ai_audit_batch_query(req: AIBatchQueryRequest, user_id: Optional[int] = Query(None)):
    """AI稽核-批量查询 — 含自动重登录机制（Token失效时自动重新登录并重试）"""
    effective_user_id = user_id or 1

    def _do_query(token: str) -> Dict[str, Any]:
        payload = req.model_dump()
        payload["access_token"] = token
        return _forward_post("/api/portal/ai-audit/batch-query", data=payload, timeout=120)

    def _check_401_error(result: Dict[str, Any]) -> bool:
        if not result or not isinstance(result, dict):
            return False
        errors = result.get("errors", [])
        return any("401" in str(err) or "Unauthorized" in str(err) for err in errors)

    access_token = _get_access_token(effective_user_id)

    if not access_token:
        logger.info(f"[batch-query] 用户{effective_user_id}无Token，尝试自动重登录...")
        relogin_result = _auto_relogin(effective_user_id)
        if relogin_result.get("success"):
            access_token = relogin_result["data"].get("access_token", "")
            logger.info(f"[batch-query] 用户{effective_user_id}自动重登录成功，使用新Token查询")
        else:
            return {
                "code": 401,
                "message": relogin_result.get("message", "未登录且自动重登录失败"),
                "data": {
                    "success": False,
                    "hint": "请手动点击'自动登录'按钮登录云门户",
                    "time_range": {"start_time": req.entry_time, "end_time": req.gate_time}
                }
            }

    result = _do_query(access_token)

    if _check_401_error(result):
        logger.warning(f"[batch-query] 用户{effective_user_id}检测到401错误，Token可能已过期，尝试自动重登录...")

        relogin_result = _auto_relogin(effective_user_id)

        if relogin_result.get("success"):
            new_token = relogin_result["data"].get("access_token", "")
            logger.info(f"[batch-query] ✅ 用户{effective_user_id}自动重登录成功！使用新Token重新查询...")

            result = _do_query(new_token)

            if _check_401_error(result):
                logger.error("[batch-query] 新Token仍然返回401错误")
                return {
                    "code": 401,
                    "message": "云门户Token已刷新但查询仍失败，请检查账号权限",
                    "data": result.get("data", {}),
                    "errors": result.get("errors", []),
                    "relogin_status": "success_but_query_failed"
                }

            logger.info(f"[batch-query] ✅ 用户{effective_user_id}使用新Token查询成功！")
            return {
                "code": 200,
                "message": "查询成功（已自动重登录并重试）",
                "data": result.get("data", {}),
                "relogin_info": {
                    "auto_relogin": True,
                    "message": "检测到Token过期，已自动重新登录并完成查询"
                }
            }
        else:
            logger.error(f"[batch-query] ❌ 用户{effective_user_id}自动重登录失败: {relogin_result.get('message')}")
            return {
                "code": 401,
                "message": f"Token已过期且自动重登录失败: {relogin_result.get('message', '未知错误')}",
                "data": result.get("data", {}),
                "errors": result.get("errors", []),
                "hint": "请手动操作: 点击'退出登录' → 输入验证码 → 重新查询"
            }

    return result


@router.post("/api/cloud-portal/ai-audit/gantry-trade")
async def ai_audit_gantry_trade(req: GantryTradeRequest, user_id: Optional[int] = Query(None)):
    """AI稽核-门架交易查询 — 直接转发至 GUI 服务"""
    payload = req.model_dump()
    payload["access_token"] = _get_access_token(user_id or 1)
    return _forward_post("/api/portal/ai-audit/gantry-trade", data=payload, timeout=60)


@router.post("/api/cloud-portal/ai-audit/gantry-plate")
async def ai_audit_gantry_plate(req: GantryPlateRequest, user_id: Optional[int] = Query(None)):
    """AI稽核-门架牌识查询 — 直接转发至 GUI 服务"""
    payload = req.model_dump()
    payload["access_token"] = _get_access_token(user_id or 1)
    return _forward_post("/api/portal/ai-audit/gantry-plate", data=payload, timeout=60)


@router.post("/api/cloud-portal/ai-audit/exit-trade")
async def ai_audit_exit_trade(req: ExitTradeRequest, user_id: Optional[int] = Query(None)):
    """AI稽核-出口交易查询 — 直接转发至 GUI 服务"""
    payload = req.model_dump()
    payload["access_token"] = _get_access_token(user_id or 1)
    return _forward_post("/api/portal/ai-audit/exit-trade", data=payload, timeout=60)


@router.post("/api/cloud-portal/ai-audit/suspected-car")
async def ai_audit_suspected_car(req: SuspectedCarRequest, user_id: Optional[int] = Query(None)):
    """AI稽核-嫌疑车查询 — 直接转发至 GUI 服务"""
    payload = req.model_dump()
    payload["access_token"] = _get_access_token(user_id or 1)
    return _forward_post("/api/portal/ai-audit/suspected-car", data=payload, timeout=60)


@router.post("/api/cloud-portal/ai-audit/audit-order")
async def ai_audit_audit_order(req: AuditOrderRequest, user_id: Optional[int] = Query(None)):
    """AI稽核-稽核工单查询 — 直接转发至 GUI 服务"""
    payload = req.model_dump()
    payload["access_token"] = _get_access_token(user_id or 1)
    return _forward_post("/api/portal/ai-audit/audit-order", data=payload, timeout=60)


@router.post("/api/cloud-portal/captcha/ocr")
async def captcha_ocr(req: OCRRequest):
    """验证码OCR识别 — 优先转发至 GUI 服务，不可用时回退到本地 ddddocr"""
    try:
        gui_result = _forward_post("/api/portal/captcha/ocr", data={"image": req.image}, timeout=15)
        if gui_result.get("code") == 200 and gui_result.get("data", {}).get("text"):
            return gui_result
    except HTTPException:
        pass
    except Exception as e:
        logger.warning(f"GUI 服务 OCR 请求失败，尝试本地回退: {e}")

    local_result = _local_ocr_classify(req.image)
    if local_result:
        logger.info(f"本地 OCR 识别成功: {local_result}")
        return {"code": 200, "message": "OCR识别成功（本地）", "data": {"text": local_result}}

    return {"code": 500, "message": "OCR识别失败，GUI服务和本地引擎均不可用", "data": None}


@router.get("/api/cloud-portal/captcha/ocr/status")
async def captcha_ocr_status():
    """OCR功能状态检查 — 合并 GUI 服务和本地引擎状态"""
    gui_status = None
    try:
        gui_status = _forward_get("/api/portal/captcha/ocr/status", timeout=5)
    except Exception:
        pass

    local_available = _local_ocr_available_func()

    gui_ocr_available = False
    if gui_status and gui_status.get("code") == 200:
        gui_ocr_available = gui_status.get("data", {}).get("available", False)

    overall_available = gui_ocr_available or local_available

    return {
        "code": 200,
        "message": "success",
        "data": {
            "available": overall_available,
            "gui_ocr_available": gui_ocr_available,
            "local_ocr_available": local_available,
            "message": "OCR功能可用" if overall_available else "OCR功能不可用",
        },
    }


@router.post("/api/cloud-portal/ai-audit/original-image")
async def ai_audit_original_image(req: OriginalImageRequest, user_id: Optional[int] = Query(None)):
    """获取高清原图 — 直接转发至 GUI 服务"""
    payload = req.model_dump()
    payload["access_token"] = _get_access_token(user_id or 1)
    return _forward_post("/api/portal/ai-audit/original-image", data=payload, timeout=60)


@router.post("/api/cloud-portal/ai-audit/select-images")
async def ai_audit_select_images(req: SelectImagesRequest):
    """根据门架ID筛选图片 — 转发至 GUI 服务"""
    return _forward_post("/api/portal/ai-audit/select-images", data=req.model_dump(), timeout=15)


@router.post("/api/cloud-portal/ai-audit/save-images")
async def ai_audit_save_images(req: SaveImagesRequest):
    """AI稽核-保存稽核图片到本地数据库"""
    try:
        config = get_app_config()
        from database import get_db_connection

        with get_db_connection("CHECK_DATA_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT 1 FROM `{req.table_name}` WHERE `通行标识ID` = %s LIMIT 1",
                    (req.record_id,)
                )
                if not cursor.fetchone():
                    return {"code": 404, "message": "记录不存在", "data": {"affected_rows": 0}}

                update_fields = []
                params = []
                updated_columns = set()

                field_mapping = {
                    '查核资料1': 'image1_base64',
                    '查核资料2': 'image2_base64',
                    '复核情况': 'review_status',
                    '核查通行标识': 'check_pass_id',
                    '特情': 'special_situation',
                    '核查拆分': 'check_split',
                    '备注': 'remark',
                }

                for db_field, req_field in field_mapping.items():
                    val = getattr(req, req_field, None)
                    if val is not None:
                        update_fields.append(f"`{db_field}` = %s")
                        params.append(val)
                        updated_columns.add(db_field)

                if req.clear_empty:
                    for db_field, req_field in field_mapping.items():
                        if db_field not in updated_columns:
                            update_fields.append(f"`{db_field}` = NULL")

                if not update_fields:
                    return {"code": 400, "message": "没有需要更新的字段"}

                params.append(req.record_id)
                sql = f"UPDATE `{req.table_name}` SET {', '.join(update_fields)} WHERE `通行标识ID` = %s"
                cursor.execute(sql, params)
                conn.commit()

                affected_rows = cursor.rowcount
                if affected_rows > 0:
                    message = f"成功更新 {affected_rows} 条记录"
                else:
                    message = "记录已存在且数据未变化，无需更新"

                return {
                    "code": 200,
                    "message": message,
                    "data": {"affected_rows": affected_rows}
                }

    except Exception as e:
        logger.error(f"保存稽核图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存稽核图片失败: {str(e)}")


@router.post("/api/cloud-portal/fetch-picture")
async def fetch_picture(req: FetchPictureRequest, user_id: Optional[int] = Query(None)):
    """代理获取云门户图片 — 转发至 GUI 服务"""
    payload = req.model_dump()
    payload["access_token"] = _get_access_token(user_id or 1)
    return _forward_post("/api/portal/fetch-picture", data=payload, timeout=60)


@router.post("/api/cloud-portal/ai-audit/branch-centers")
async def ai_audit_branch_centers():
    """获取分中心列表 — 转发至 GUI 服务"""
    return _forward_post("/api/portal/ai-audit/branch-centers", timeout=15)


@router.post("/api/cloud-portal/ai-audit/road-sections")
async def ai_audit_road_sections():
    """获取路段列表 — 转发至 GUI 服务"""
    return _forward_post("/api/portal/ai-audit/road-sections", timeout=15)


@router.post("/api/cloud-portal/ai-audit/gantry-list")
async def ai_audit_gantry_list():
    """获取门架列表 — 转发至 GUI 服务"""
    return _forward_post("/api/portal/ai-audit/gantry-list", timeout=15)


@router.get("/api/cloud-portal/ai-audit/order-detail")
async def ai_audit_order_detail(order_id: str, user_id: Optional[int] = Query(None)):
    """AI稽核-工单详情 — 转发至 GUI 服务"""
    params = {"order_id": order_id, "access_token": _get_access_token(user_id or 1)}
    return _forward_get("/api/portal/order-detail", params=params, timeout=60)


@router.get("/api/cloud-portal/order-detail")
async def get_order_detail(order_id: str, user_id: Optional[int] = Query(None)):
    """获取工单详情 — 转发至 GUI 服务"""
    params = {"order_id": order_id, "access_token": _get_access_token(user_id or 1)}
    return _forward_get("/api/portal/order-detail", params=params, timeout=60)


@router.get("/api/cloud-portal/request-logs")
async def get_request_logs():
    """获取请求日志 — 转发至 GUI 服务"""
    return _forward_get("/api/portal/request-logs", timeout=10)


@router.get("/api/cloud-portal/request-info")
async def get_request_info():
    """获取请求信息 — 转发至 GUI 服务"""
    return _forward_get("/api/portal/request-info", timeout=10)


@router.get("/api/cloud-portal/latest-response")
async def get_latest_response():
    """获取最新响应 — 转发至 GUI 服务"""
    return _forward_get("/api/portal/latest-response", timeout=10)


# ==================== 云门户账号管理（MySQL system_db.portal_accounts） ====================


@router.post("/api/cloud-portal/account/save")
async def save_cloud_portal_account(req: AccountSaveRequest, user_id: Optional[int] = Query(None)):
    """保存云门户账号"""
    try:
        _save_account(user_id or 1, req.portal_username, req.portal_password)
        return {"code": 200, "message": "账号保存成功", "data": None}
    except Exception as e:
        logger.error(f"保存账号失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存账号失败: {str(e)}")


@router.get("/api/cloud-portal/account")
async def get_cloud_portal_account(user_id: Optional[int] = Query(None)):
    """获取云门户账号"""
    account = _get_account(user_id or 1)
    if account:
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "portal_username": account["portal_username"],
                "portal_password": account["portal_password"],
                "access_token": account.get("access_token"),
                "refresh_token": account.get("refresh_token"),
                "redirect_uri": account.get("redirect_uri"),
                "token_expires_at": account.get("token_expires_at"),
                "is_valid": _is_token_valid(account),
            },
        }
    return {"code": 200, "message": "未保存账号", "data": None}


@router.delete("/api/cloud-portal/account")
async def delete_cloud_portal_account(user_id: Optional[int] = Query(None)):
    """删除云门户账号"""
    _delete_account(user_id or 1)
    return {"code": 200, "message": "账号已删除", "data": None}


# ==================== 前端兼容路由（/api/cloud-portal-account/） ====================


@router.get("/api/cloud-portal-account/")
async def get_cloud_portal_account_v2(user_id: Optional[int] = Query(None)):
    """获取云门户账号（前端兼容路径）"""
    effective_user_id = user_id or 1
    account = _get_account(effective_user_id)
    if account:
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "id": account["id"],
                "user_id": account["user_id"],
                "portal_username": account["portal_username"],
                "has_password": bool(account["portal_password"]),
                "created_at": str(account["created_at"]) if account.get("created_at") else None,
                "updated_at": str(account["updated_at"]) if account.get("updated_at") else None,
            },
        }
    return {"code": 200, "message": "未保存账号", "data": None}


@router.post("/api/cloud-portal-account/")
async def save_cloud_portal_account_v2(req: AccountSaveRequest, user_id: Optional[int] = Query(None)):
    """保存云门户账号（前端兼容路径）"""
    try:
        _save_account(user_id or 1, req.portal_username, req.portal_password)
        return {"code": 200, "message": "账号保存成功", "data": None}
    except Exception as e:
        logger.error(f"保存账号失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存账号失败: {str(e)}")


@router.delete("/api/cloud-portal-account/")
async def delete_cloud_portal_account_v2(user_id: Optional[int] = Query(None)):
    """删除云门户账号（前端兼容路径）"""
    _delete_account(user_id or 1)
    return {"code": 200, "message": "账号已删除", "data": None}


@router.get("/api/cloud-portal-account/credentials")
async def get_cloud_portal_credentials(user_id: Optional[int] = Query(None)):
    """获取云门户凭证（含密码和Token信息）"""
    effective_user_id = user_id or 1
    account = _get_account(effective_user_id)
    if account:
        is_valid = _is_token_valid(account)

        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "portal_username": account["portal_username"],
                "portal_password": account["portal_password"],
                "access_token": account.get("access_token"),
                "refresh_token": account.get("refresh_token"),
                "redirect_uri": account.get("redirect_uri"),
                "token_expires_at": account.get("token_expires_at"),
                "token_valid": is_valid,
            },
        }
    return {"code": 200, "message": "未保存账号", "data": None}


