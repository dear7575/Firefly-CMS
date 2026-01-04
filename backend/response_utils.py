"""
响应格式工具
统一返回结构：code/msg/data
"""
from typing import Any, Dict, Optional, Tuple


def is_standard_payload(payload: Any) -> bool:
    """判断是否已是标准响应结构"""
    return isinstance(payload, dict) and "code" in payload and "msg" in payload and "data" in payload


def build_response(code: int, msg: str, data: Any = None) -> Dict[str, Any]:
    """构建标准响应结构"""
    return {
        "code": code,
        "msg": msg,
        "data": data
    }


def build_error(
    status_code: int,
    msg: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """构建标准错误响应结构"""
    data = {}
    if error_code:
        data["error_code"] = error_code
    if details:
        data["details"] = details
    if not data:
        data = None
    return build_response(status_code, msg, data)


def default_success_message(method: str, status_code: int) -> str:
    """根据请求方法给出默认成功文案"""
    if status_code >= 400:
        return "请求失败"
    method = (method or "").upper()
    if method == "GET":
        return "查询成功"
    if method == "POST":
        return "新增成功"
    if method in ("PUT", "PATCH"):
        return "更新成功"
    if method == "DELETE":
        return "删除成功"
    return "操作成功"


def extract_message_and_data(
    payload: Any,
    method: str,
    status_code: int
) -> Tuple[str, Any]:
    """从已有响应中提取 msg 与 data"""
    default_msg = default_success_message(method, status_code)

    if isinstance(payload, dict):
        if "message" in payload:
            msg = payload.get("message") or default_msg
            data = {k: v for k, v in payload.items() if k != "message"}
            if not data:
                data = None
            return msg, data

        if "detail" in payload and len(payload) == 1:
            msg = payload.get("detail") or default_msg
            return msg, None

        if "success" in payload and "error" in payload:
            error = payload.get("error") or {}
            msg = error.get("message") or default_msg
            data = {}
            if isinstance(error, dict):
                if error.get("code"):
                    data["error_code"] = error.get("code")
                if error.get("details"):
                    data["details"] = error.get("details")
            if not data:
                data = None
            return msg, data

        return default_msg, payload

    if isinstance(payload, list):
        return default_msg, payload

    return default_msg, payload


def normalize_payload(payload: Any, method: str, status_code: int) -> Dict[str, Any]:
    """将任意响应体标准化为 code/msg/data"""
    if is_standard_payload(payload):
        return payload
    msg, data = extract_message_and_data(payload, method, status_code)
    return build_response(status_code, msg, data)
