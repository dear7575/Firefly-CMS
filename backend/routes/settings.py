"""
站点设置路由模块
提供站点设置的增删改查 API 接口
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import models
from database import get_db
from routes.posts import get_current_user

router = APIRouter(prefix="/settings", tags=["站点设置"])


# ============== 数据模型 ==============

class SettingCreate(BaseModel):
    """创建设置请求模型"""
    key: str = Field(..., min_length=1, max_length=100, description="设置键名")
    value: Optional[str] = Field(None, description="设置值")
    type: str = Field(default="string", description="值类型")
    group: str = Field(default="general", description="设置分组")
    label: Optional[str] = Field(None, max_length=100, description="显示标签")
    description: Optional[str] = Field(None, description="设置描述")
    sort_order: int = Field(default=0, description="排序权重")


class SettingUpdate(BaseModel):
    """更新设置请求模型"""
    value: Optional[str] = Field(None, description="设置值")
    label: Optional[str] = Field(None, max_length=100, description="显示标签")
    description: Optional[str] = Field(None, description="设置描述")
    sort_order: Optional[int] = Field(None, description="排序权重")


class SettingResponse(BaseModel):
    """设置响应模型"""
    id: str
    key: str
    value: Optional[str]
    type: str
    group: str
    label: Optional[str]
    description: Optional[str]
    sort_order: int
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SettingBatchUpdate(BaseModel):
    """批量更新设置请求模型"""
    settings: Dict[str, Any] = Field(..., description="设置键值对")


# ============== 公开 API 接口（无需认证） ==============

@router.get("/public", summary="获取公开站点配置")
def get_public_settings(db: Session = Depends(get_db)):
    """
    获取公开的站点配置（无需认证）
    返回格式化的配置对象，方便前端直接使用
    """
    settings = db.query(models.SiteSetting).all()

    # 转换为键值对格式
    result = {}
    for setting in settings:
        # 根据类型转换值
        value = setting.value
        if setting.type == "boolean":
            value = value.lower() == "true" if value else False
        elif setting.type == "number":
            try:
                value = int(value) if value else 0
            except ValueError:
                try:
                    value = float(value) if value else 0.0
                except ValueError:
                    value = 0
        elif setting.type == "json":
            try:
                value = json.loads(value) if value else None
            except json.JSONDecodeError:
                value = None

        result[setting.key] = value

    return result


@router.get("/public/grouped", summary="获取分组的公开站点配置")
def get_public_settings_grouped(db: Session = Depends(get_db)):
    """
    获取按分组组织的公开站点配置（无需认证）
    返回按 group 分组的配置对象
    """
    settings = db.query(models.SiteSetting).order_by(
        models.SiteSetting.group,
        models.SiteSetting.sort_order.desc()
    ).all()

    # 按分组组织
    grouped = {}
    for setting in settings:
        group = setting.group or "general"
        if group not in grouped:
            grouped[group] = {}

        # 根据类型转换值
        value = setting.value
        if setting.type == "boolean":
            value = value.lower() == "true" if value else False
        elif setting.type == "number":
            try:
                value = int(value) if value else 0
            except ValueError:
                try:
                    value = float(value) if value else 0.0
                except ValueError:
                    value = 0
        elif setting.type == "json":
            try:
                value = json.loads(value) if value else None
            except json.JSONDecodeError:
                value = None

        # 使用简化的键名（去掉分组前缀）
        key = setting.key
        if key.startswith(group + "_"):
            key = key[len(group) + 1:]

        grouped[group][key] = value

    return grouped


@router.get("/public/by-group/{group}", summary="获取指定分组的公开配置")
def get_public_settings_by_group(group: str, db: Session = Depends(get_db)):
    """
    获取指定分组的公开站点配置（无需认证）
    """
    settings = db.query(models.SiteSetting).filter(
        models.SiteSetting.group == group
    ).order_by(models.SiteSetting.sort_order.desc()).all()

    result = {}
    for setting in settings:
        # 根据类型转换值
        value = setting.value
        if setting.type == "boolean":
            value = value.lower() == "true" if value else False
        elif setting.type == "number":
            try:
                value = int(value) if value else 0
            except ValueError:
                try:
                    value = float(value) if value else 0.0
                except ValueError:
                    value = 0
        elif setting.type == "json":
            try:
                value = json.loads(value) if value else None
            except json.JSONDecodeError:
                value = None

        # 使用简化的键名（去掉分组前缀）
        key = setting.key
        if key.startswith(group + "_"):
            key = key[len(group) + 1:]

        result[key] = value

    return result


# ============== 需要认证的 API 接口 ==============

@router.get("", response_model=List[SettingResponse], summary="获取所有设置")
def get_settings(
    group: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取所有站点设置"""
    query = db.query(models.SiteSetting)
    if group:
        query = query.filter(models.SiteSetting.group == group)

    settings = query.order_by(
        models.SiteSetting.group,
        models.SiteSetting.sort_order.desc()
    ).all()
    return settings


@router.get("/groups", summary="获取设置分组列表")
def get_setting_groups(db: Session = Depends(get_db)):
    """获取所有设置分组"""
    groups = db.query(models.SiteSetting.group).distinct().all()
    return [g[0] for g in groups]


# ============== 公告管理 API 接口（放在通用路由之前避免路由冲突） ==============

class AnnouncementConfig(BaseModel):
    """公告配置模型"""
    title: str = Field(default="公告", description="公告标题")
    content: str = Field(..., description="公告内容")
    closable: bool = Field(default=True, description="是否可关闭")
    link_enable: bool = Field(default=False, description="是否启用链接")
    link_text: str = Field(default="了解更多", description="链接文本")
    link_url: str = Field(default="/about", description="链接URL")
    link_external: bool = Field(default=False, description="是否为外部链接")


@router.get("/announcement", summary="获取公告配置")
def get_announcement_config(db: Session = Depends(get_db)):
    """获取当前公告配置（公开接口）"""
    # 从数据库读取公告配置
    settings_map = {}
    announcement_keys = [
        "announcement_title",
        "announcement_content",
        "announcement_closable",
        "announcement_link_enable",
        "announcement_link_text",
        "announcement_link_url",
        "announcement_link_external"
    ]
    
    settings = db.query(models.SiteSetting).filter(
        models.SiteSetting.key.in_(announcement_keys)
    ).all()
    
    for setting in settings:
        key = setting.key.replace("announcement_", "")
        value = setting.value
        
        # 类型转换
        if setting.type == "boolean":
            value = value.lower() == "true" if value else False
        
        settings_map[key] = value
    
    # 如果没有配置，返回默认值
    if not settings_map:
        return {
            "title": "公告",
            "content": "欢迎来到我的博客！这是一则示例公告。",
            "closable": True,
            "link": {
                "enable": False,
                "text": "了解更多",
                "url": "/about",
                "external": False
            }
        }
    
    # 构建响应，使用嵌套的 link 对象
    return {
        "title": settings_map.get("title", "公告"),
        "content": settings_map.get("content", ""),
        "closable": settings_map.get("closable", True),
        "link": {
            "enable": settings_map.get("link_enable", False),
            "text": settings_map.get("link_text", "了解更多"),
            "url": settings_map.get("link_url", "/about"),
            "external": settings_map.get("link_external", False)
        }
    }


@router.put("/announcement", summary="更新公告配置")
def update_announcement_config(
    config: AnnouncementConfig,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """更新公告配置（需要认证）"""
    # 定义要更新的配置项
    settings_to_update = {
        "announcement_title": (config.title, "string", "announcement"),
        "announcement_content": (config.content, "string", "announcement"),
        "announcement_closable": (str(config.closable), "boolean", "announcement"),
        "announcement_link_enable": (str(config.link_enable), "boolean", "announcement"),
        "announcement_link_text": (config.link_text, "string", "announcement"),
        "announcement_link_url": (config.link_url, "string", "announcement"),
        "announcement_link_external": (str(config.link_external), "boolean", "announcement"),
    }
    
    updated = 0
    created = 0
    
    for key, (value, type_str, group) in settings_to_update.items():
        setting = db.query(models.SiteSetting).filter(
            models.SiteSetting.key == key
        ).first()
        
        if setting:
            setting.value = value
            updated += 1
        else:
            new_setting = models.SiteSetting(
                key=key,
                value=value,
                type=type_str,
                group=group,
                label=key.replace("announcement_", "").replace("_", " ").title()
            )
            db.add(new_setting)
            created += 1
    
    db.commit()
    
    return {
        "message": "公告配置更新成功",
        "updated": updated,
        "created": created
    }


@router.get("/by-key/{key}", response_model=SettingResponse, summary="根据键名获取设置")
def get_setting_by_key(key: str, db: Session = Depends(get_db)):
    """根据键名获取单个设置"""
    setting = db.query(models.SiteSetting).filter(
        models.SiteSetting.key == key
    ).first()
    if not setting:
        raise HTTPException(status_code=404, detail="设置不存在")
    return setting


@router.get("/{setting_id}", response_model=SettingResponse, summary="获取单个设置")
def get_setting(setting_id: str, db: Session = Depends(get_db)):
    """根据ID获取设置详情"""
    setting = db.query(models.SiteSetting).filter(
        models.SiteSetting.id == setting_id
    ).first()
    if not setting:
        raise HTTPException(status_code=404, detail="设置不存在")
    return setting


@router.post("", status_code=status.HTTP_201_CREATED, summary="创建设置")
def create_setting(
    setting: SettingCreate,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """创建新设置项"""
    # 检查键名是否已存在
    existing = db.query(models.SiteSetting).filter(
        models.SiteSetting.key == setting.key
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="设置键名已存在")

    db_setting = models.SiteSetting(
        key=setting.key,
        value=setting.value,
        type=setting.type,
        group=setting.group,
        label=setting.label,
        description=setting.description,
        sort_order=setting.sort_order
    )

    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)

    return {"message": "设置创建成功", "id": db_setting.id}


@router.put("/by-key/{key}", summary="根据键名更新设置")
def update_setting_by_key(
    key: str,
    setting: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """根据键名更新设置"""
    db_setting = db.query(models.SiteSetting).filter(
        models.SiteSetting.key == key
    ).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail="设置不存在")

    # 更新字段
    update_data = setting.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(db_setting, k, v)

    db.commit()
    return {"message": "设置更新成功"}


@router.put("/{setting_id}", summary="更新设置")
def update_setting(
    setting_id: str,
    setting: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """更新设置信息"""
    db_setting = db.query(models.SiteSetting).filter(
        models.SiteSetting.id == setting_id
    ).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail="设置不存在")

    # 更新字段
    update_data = setting.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_setting, key, value)

    db.commit()
    return {"message": "设置更新成功"}


@router.post("/batch", summary="批量更新设置")
def batch_update_settings(
    data: SettingBatchUpdate,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """批量更新设置（根据键名）"""
    updated_count = 0
    created_count = 0

    for key, value in data.settings.items():
        db_setting = db.query(models.SiteSetting).filter(
            models.SiteSetting.key == key
        ).first()

        # 将值转换为字符串存储
        str_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)

        if db_setting:
            db_setting.value = str_value
            updated_count += 1
        else:
            # 自动创建不存在的设置
            new_setting = models.SiteSetting(
                key=key,
                value=str_value,
                type="json" if isinstance(value, (dict, list)) else "string",
                group="general"
            )
            db.add(new_setting)
            created_count += 1

    db.commit()
    return {
        "message": "批量更新成功",
        "updated": updated_count,
        "created": created_count
    }


@router.delete("/{setting_id}", summary="删除设置")
def delete_setting(
    setting_id: str,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """删除设置项"""
    db_setting = db.query(models.SiteSetting).filter(
        models.SiteSetting.id == setting_id
    ).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail="设置不存在")

    db.delete(db_setting)
    db.commit()
    return {"message": "设置删除成功"}


@router.post("/init", summary="初始化默认设置")
def init_default_settings(
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """初始化默认站点设置"""
    default_settings = [
        # 基本信息
        {"key": "site_title", "value": "Firefly", "type": "string", "group": "basic", "label": "站点标题", "sort_order": 100},
        {"key": "site_subtitle", "value": "A beautiful blog", "type": "string", "group": "basic", "label": "站点副标题", "sort_order": 99},
        {"key": "site_description", "value": "", "type": "text", "group": "basic", "label": "站点描述", "sort_order": 98},
        {"key": "site_keywords", "value": "", "type": "string", "group": "basic", "label": "站点关键词", "sort_order": 97},
        {"key": "site_url", "value": "", "type": "string", "group": "basic", "label": "站点URL", "sort_order": 96},

        # 个人资料
        {"key": "profile_avatar", "value": "/assets/images/avatar.webp", "type": "string", "group": "profile", "label": "头像", "sort_order": 100},
        {"key": "profile_name", "value": "Firefly", "type": "string", "group": "profile", "label": "昵称", "sort_order": 99},
        {"key": "profile_bio", "value": "Hello, I'm Firefly.", "type": "text", "group": "profile", "label": "个人签名", "sort_order": 98},

        # 页脚设置
        {"key": "footer_icp", "value": "", "type": "string", "group": "footer", "label": "ICP备案号", "sort_order": 100},
        {"key": "footer_icp_url", "value": "https://beian.miit.gov.cn/", "type": "string", "group": "footer", "label": "备案链接", "sort_order": 99},
        {"key": "footer_copyright", "value": "", "type": "string", "group": "footer", "label": "版权信息", "sort_order": 98},
        {"key": "footer_powered_by", "value": "true", "type": "boolean", "group": "footer", "label": "显示Powered by", "sort_order": 97},

        # 主题设置
        {"key": "theme_hue", "value": "165", "type": "number", "group": "theme", "label": "主题色相", "sort_order": 100},
        {"key": "theme_fixed", "value": "false", "type": "boolean", "group": "theme", "label": "固定主题色", "sort_order": 99},
        {"key": "theme_default_mode", "value": "system", "type": "string", "group": "theme", "label": "默认主题模式", "sort_order": 98},

        # 导航栏设置
        {"key": "brand_navbar_layout", "value": "space-between", "type": "string", "group": "brand", "label": "导航栏布局", "description": "left=左对齐, center=居中, space-between=两端对齐", "sort_order": 95},
        {"key": "brand_navbar_width_full", "value": "false", "type": "boolean", "group": "brand", "label": "导航栏全宽", "sort_order": 94},
    ]

    created_count = 0
    for setting_data in default_settings:
        existing = db.query(models.SiteSetting).filter(
            models.SiteSetting.key == setting_data["key"]
        ).first()
        if not existing:
            db_setting = models.SiteSetting(**setting_data)
            db.add(db_setting)
            created_count += 1

    db.commit()
    return {"message": f"初始化完成，创建了 {created_count} 个设置项"}


# ============== 公告管理 API 接口 ==============

class AnnouncementConfig(BaseModel):
    """公告配置模型"""
    title: str = Field(default="公告", description="公告标题")
    content: str = Field(..., description="公告内容")
    closable: bool = Field(default=True, description="是否可关闭")
    link_enable: bool = Field(default=False, description="是否启用链接")
    link_text: str = Field(default="了解更多", description="链接文本")
    link_url: str = Field(default="/about", description="链接URL")
    link_external: bool = Field(default=False, description="是否为外部链接")


@router.get("/announcement", summary="获取公告配置")
def get_announcement_config(db: Session = Depends(get_db)):
    """获取当前公告配置（公开接口）"""
    # 从数据库读取公告配置
    settings_map = {}
    announcement_keys = [
        "announcement_title",
        "announcement_content",
        "announcement_closable",
        "announcement_link_enable",
        "announcement_link_text",
        "announcement_link_url",
        "announcement_link_external"
    ]
    
    settings = db.query(models.SiteSetting).filter(
        models.SiteSetting.key.in_(announcement_keys)
    ).all()
    
    for setting in settings:
        key = setting.key.replace("announcement_", "")
        value = setting.value
        
        # 类型转换
        if setting.type == "boolean":
            value = value.lower() == "true" if value else False
        
        settings_map[key] = value
    
    # 如果没有配置，返回默认值
    if not settings_map:
        return {
            "title": "公告",
            "content": "欢迎来到我的博客！这是一则示例公告。",
            "closable": True,
            "link_enable": True,
            "link_text": "了解更多",
            "link_url": "/about",
            "link_external": False
        }
    
    # 构建响应，使用下划线命名以匹配前端配置
    return {
        "title": settings_map.get("title", "公告"),
        "content": settings_map.get("content", ""),
        "closable": settings_map.get("closable", True),
        "link": {
            "enable": settings_map.get("link_enable", False),
            "text": settings_map.get("link_text", "了解更多"),
            "url": settings_map.get("link_url", "/about"),
            "external": settings_map.get("link_external", False)
        }
    }


@router.put("/announcement", summary="更新公告配置")
def update_announcement_config(
    config: AnnouncementConfig,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """更新公告配置（需要认证）"""
    # 定义要更新的配置项
    settings_to_update = {
        "announcement_title": (config.title, "string", "announcement"),
        "announcement_content": (config.content, "string", "announcement"),
        "announcement_closable": (str(config.closable), "boolean", "announcement"),
        "announcement_link_enable": (str(config.link_enable), "boolean", "announcement"),
        "announcement_link_text": (config.link_text, "string", "announcement"),
        "announcement_link_url": (config.link_url, "string", "announcement"),
        "announcement_link_external": (str(config.link_external), "boolean", "announcement"),
    }
    
    updated = 0
    created = 0
    
    for key, (value, type_str, group) in settings_to_update.items():
        setting = db.query(models.SiteSetting).filter(
            models.SiteSetting.key == key
        ).first()
        
        if setting:
            setting.value = value
            updated += 1
        else:
            new_setting = models.SiteSetting(
                key=key,
                value=value,
                type=type_str,
                group=group,
                label=key.replace("announcement_", "").replace("_", " ").title()
            )
            db.add(new_setting)
            created += 1
    
    db.commit()
    
    return {
        "message": "公告配置更新成功",
        "updated": updated,
        "created": created
    }
