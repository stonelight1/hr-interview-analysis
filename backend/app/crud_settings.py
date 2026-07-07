import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import constants
from app.models import AiPromptTemplate, JobTypeConfig
from app.services.prompt_templates import DEFAULT_PROMPT_TEMPLATES, get_default_prompt_template


DEFAULT_JOB_TYPE_ORDER = [
    constants.JOB_TYPE_SALES,
    constants.JOB_TYPE_ECOMMERCE,
    constants.JOB_TYPE_CUSTOMER_SERVICE,
    constants.JOB_TYPE_ADMIN_HR,
    constants.JOB_TYPE_FINANCE,
    constants.JOB_TYPE_WAREHOUSE,
    constants.JOB_TYPE_INSTALLATION,
    constants.JOB_TYPE_ENTRY_LEVEL_MGMT,
    constants.JOB_TYPE_GENERAL,
]


def _dump_json(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False)


def _load_json_list(value: Optional[str]) -> list:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _serialize_job_type(row: JobTypeConfig) -> Dict[str, Any]:
    return {
        "id": row.id,
        "type_name": row.type_name,
        "description": row.description,
        "evaluation_focus": _load_json_list(row.evaluation_focus_json),
        "enabled": bool(row.enabled),
        "sort_order": row.sort_order or 0,
        "builtin": bool(row.builtin),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def ensure_default_job_types(db: Session) -> None:
    existing_names = {
        item.type_name
        for item in db.query(JobTypeConfig).all()
    }
    created = False
    for index, type_name in enumerate(DEFAULT_JOB_TYPE_ORDER, start=1):
        if type_name in existing_names:
            continue
        db.add(
            JobTypeConfig(
                type_name=type_name,
                description="系统内置岗位类型，可按业务需要调整筛选重点。",
                evaluation_focus_json=_dump_json(constants.JOB_TYPE_EVALUATION_FOCUS.get(type_name, [])),
                enabled=1,
                sort_order=index,
                builtin=1,
            )
        )
        created = True
    if created:
        db.commit()


def list_job_type_configs(
    db: Session,
    keyword: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    ensure_default_job_types(db)
    query = db.query(JobTypeConfig).filter(JobTypeConfig.deleted == 0)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                JobTypeConfig.type_name.ilike(pattern),
                JobTypeConfig.description.ilike(pattern),
            )
        )
    if enabled is not None:
        query = query.filter(JobTypeConfig.enabled == (1 if enabled else 0))
    items = query.order_by(JobTypeConfig.sort_order.asc(), JobTypeConfig.id.asc()).all()
    return {"total": len(items), "items": [_serialize_job_type(item) for item in items]}


def get_enabled_job_types(db: Session) -> Dict[str, Any]:
    rows = list_job_type_configs(db, enabled=True)["items"]
    return {
        "job_types": [item["type_name"] for item in rows],
        "evaluation_focus": {
            item["type_name"]: item["evaluation_focus"]
            for item in rows
        },
        "items": rows,
    }


def create_job_type_config(db: Session, data: dict) -> Dict[str, Any]:
    type_name = (data.get("type_name") or "").strip()
    if not type_name:
        raise ValueError("岗位类型名称不能为空")
    existing = (
        db.query(JobTypeConfig)
        .filter(JobTypeConfig.type_name == type_name, JobTypeConfig.deleted == 0)
        .first()
    )
    if existing:
        raise ValueError("岗位类型已存在")

    row = JobTypeConfig(
        type_name=type_name,
        description=data.get("description"),
        evaluation_focus_json=_dump_json(data.get("evaluation_focus") or []),
        enabled=1 if data.get("enabled", True) else 0,
        sort_order=data.get("sort_order") or 0,
        builtin=0,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize_job_type(row)


def update_job_type_config(db: Session, config_id: int, data: dict) -> Optional[Dict[str, Any]]:
    row = db.query(JobTypeConfig).filter(JobTypeConfig.id == config_id, JobTypeConfig.deleted == 0).first()
    if not row:
        return None
    if "type_name" in data and data["type_name"] is not None:
        type_name = data["type_name"].strip()
        if not type_name:
            raise ValueError("岗位类型名称不能为空")
        existing = (
            db.query(JobTypeConfig)
            .filter(JobTypeConfig.id != config_id, JobTypeConfig.type_name == type_name, JobTypeConfig.deleted == 0)
            .first()
        )
        if existing:
            raise ValueError("岗位类型已存在")
        row.type_name = type_name
    if "description" in data:
        row.description = data.get("description")
    if "evaluation_focus" in data and data["evaluation_focus"] is not None:
        row.evaluation_focus_json = _dump_json(data.get("evaluation_focus") or [])
    if "enabled" in data and data["enabled"] is not None:
        row.enabled = 1 if data["enabled"] else 0
    if "sort_order" in data and data["sort_order"] is not None:
        row.sort_order = data["sort_order"]
    row.updated_at = datetime.now()
    db.commit()
    db.refresh(row)
    return _serialize_job_type(row)


def archive_job_type_config(db: Session, config_id: int) -> Optional[Dict[str, Any]]:
    row = db.query(JobTypeConfig).filter(JobTypeConfig.id == config_id, JobTypeConfig.deleted == 0).first()
    if not row:
        return None
    row.enabled = 0
    row.deleted = 1
    row.updated_at = datetime.now()
    db.commit()
    db.refresh(row)
    return _serialize_job_type(row)


def _serialize_prompt(row: AiPromptTemplate) -> Dict[str, Any]:
    return {
        "id": row.id,
        "prompt_key": row.prompt_key,
        "prompt_name": row.prompt_name,
        "scene": row.scene,
        "system_prompt": row.system_prompt,
        "user_prompt": row.user_prompt,
        "version": row.version or 1,
        "status": row.status,
        "builtin": bool(row.builtin),
        "remark": row.remark,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def ensure_default_prompt_templates(db: Session) -> None:
    created = False
    for prompt_key, template in DEFAULT_PROMPT_TEMPLATES.items():
        existing = (
            db.query(AiPromptTemplate)
            .filter(AiPromptTemplate.prompt_key == prompt_key, AiPromptTemplate.deleted == 0)
            .first()
        )
        if existing:
            continue
        db.add(
            AiPromptTemplate(
                prompt_key=prompt_key,
                prompt_name=template["prompt_name"],
                scene=template.get("scene"),
                system_prompt=template.get("system_prompt"),
                user_prompt=template["user_prompt"],
                version=1,
                status=constants.PROMPT_STATUS_ACTIVE,
                builtin=1,
                remark="系统默认模板",
            )
        )
        created = True
    if created:
        db.commit()


def list_ai_prompt_templates(
    db: Session,
    keyword: Optional[str] = None,
    prompt_key: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    ensure_default_prompt_templates(db)
    query = db.query(AiPromptTemplate).filter(AiPromptTemplate.deleted == 0)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                AiPromptTemplate.prompt_name.ilike(pattern),
                AiPromptTemplate.prompt_key.ilike(pattern),
                AiPromptTemplate.scene.ilike(pattern),
                AiPromptTemplate.remark.ilike(pattern),
            )
        )
    if prompt_key:
        query = query.filter(AiPromptTemplate.prompt_key == prompt_key)
    if status:
        query = query.filter(AiPromptTemplate.status == status)
    rows = (
        query.order_by(
            AiPromptTemplate.prompt_key.asc(),
            AiPromptTemplate.version.desc(),
            AiPromptTemplate.id.desc(),
        )
        .all()
    )
    return {"total": len(rows), "items": [_serialize_prompt(row) for row in rows]}


def _next_prompt_version(db: Session, prompt_key: str) -> int:
    rows = (
        db.query(AiPromptTemplate)
        .filter(AiPromptTemplate.prompt_key == prompt_key, AiPromptTemplate.deleted == 0)
        .all()
    )
    versions = [row.version or 1 for row in rows]
    return (max(versions) if versions else 0) + 1


def create_ai_prompt_template(db: Session, data: dict) -> Dict[str, Any]:
    prompt_key = (data.get("prompt_key") or "").strip()
    if prompt_key not in constants.VALID_PROMPT_KEYS:
        raise ValueError("不支持的提示词类型")
    row = AiPromptTemplate(
        prompt_key=prompt_key,
        prompt_name=(data.get("prompt_name") or "").strip(),
        scene=data.get("scene"),
        system_prompt=data.get("system_prompt"),
        user_prompt=data.get("user_prompt"),
        version=_next_prompt_version(db, prompt_key),
        status=constants.PROMPT_STATUS_DRAFT,
        builtin=0,
        remark=data.get("remark"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize_prompt(row)


def update_ai_prompt_template(db: Session, prompt_id: int, data: dict) -> Optional[Dict[str, Any]]:
    row = db.query(AiPromptTemplate).filter(AiPromptTemplate.id == prompt_id, AiPromptTemplate.deleted == 0).first()
    if not row:
        return None
    for key in ("prompt_name", "scene", "system_prompt", "user_prompt", "remark"):
        if key in data and data[key] is not None:
            setattr(row, key, data[key])
    row.updated_at = datetime.now()
    db.commit()
    db.refresh(row)
    return _serialize_prompt(row)


def copy_ai_prompt_template(db: Session, prompt_id: int) -> Optional[Dict[str, Any]]:
    source = db.query(AiPromptTemplate).filter(AiPromptTemplate.id == prompt_id, AiPromptTemplate.deleted == 0).first()
    if not source:
        return None
    row = AiPromptTemplate(
        prompt_key=source.prompt_key,
        prompt_name=f"{source.prompt_name} 副本",
        scene=source.scene,
        system_prompt=source.system_prompt,
        user_prompt=source.user_prompt,
        version=_next_prompt_version(db, source.prompt_key),
        status=constants.PROMPT_STATUS_DRAFT,
        builtin=0,
        remark=source.remark,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize_prompt(row)


def activate_ai_prompt_template(db: Session, prompt_id: int) -> Optional[Dict[str, Any]]:
    row = db.query(AiPromptTemplate).filter(AiPromptTemplate.id == prompt_id, AiPromptTemplate.deleted == 0).first()
    if not row:
        return None
    (
        db.query(AiPromptTemplate)
        .filter(
            AiPromptTemplate.prompt_key == row.prompt_key,
            AiPromptTemplate.deleted == 0,
            AiPromptTemplate.status == constants.PROMPT_STATUS_ACTIVE,
        )
        .update({"status": constants.PROMPT_STATUS_DRAFT, "updated_at": datetime.now()})
    )
    row.status = constants.PROMPT_STATUS_ACTIVE
    row.updated_at = datetime.now()
    db.commit()
    db.refresh(row)
    return _serialize_prompt(row)


def archive_ai_prompt_template(db: Session, prompt_id: int) -> Optional[Dict[str, Any]]:
    row = db.query(AiPromptTemplate).filter(AiPromptTemplate.id == prompt_id, AiPromptTemplate.deleted == 0).first()
    if not row:
        return None
    row.status = constants.PROMPT_STATUS_ARCHIVED
    row.deleted = 1
    row.updated_at = datetime.now()
    db.commit()
    db.refresh(row)
    return _serialize_prompt(row)


def reset_ai_prompt_template(db: Session, prompt_key: str) -> Dict[str, Any]:
    if prompt_key not in constants.VALID_PROMPT_KEYS:
        raise ValueError("不支持的提示词类型")
    template = get_default_prompt_template(prompt_key)
    row = AiPromptTemplate(
        prompt_key=prompt_key,
        prompt_name=template["prompt_name"],
        scene=template.get("scene"),
        system_prompt=template.get("system_prompt"),
        user_prompt=template["user_prompt"],
        version=_next_prompt_version(db, prompt_key),
        status=constants.PROMPT_STATUS_DRAFT,
        builtin=1,
        remark="从系统默认模板重置",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return activate_ai_prompt_template(db, row.id)


def get_active_prompt_pair(db: Session, prompt_key: str) -> Dict[str, Optional[str]]:
    ensure_default_prompt_templates(db)
    row = (
        db.query(AiPromptTemplate)
        .filter(
            AiPromptTemplate.prompt_key == prompt_key,
            AiPromptTemplate.status == constants.PROMPT_STATUS_ACTIVE,
            AiPromptTemplate.deleted == 0,
        )
        .order_by(AiPromptTemplate.version.desc(), AiPromptTemplate.id.desc())
        .first()
    )
    if row:
        return {
            "system_prompt": row.system_prompt,
            "user_prompt": row.user_prompt,
        }

    template = get_default_prompt_template(prompt_key)
    return {
        "system_prompt": template.get("system_prompt"),
        "user_prompt": template["user_prompt"],
    }
