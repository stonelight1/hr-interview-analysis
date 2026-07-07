"""
JD AI 解析服务

支持将粘贴的完整 JD 文本自动解析为结构化岗位信息。
AI 不编造信息，未提供的字段返回空值。
"""
import json
import logging
from typing import Dict, Any, Optional

from app.services.deepseek_client import call_deepseek
from app.services.prompt_templates import get_default_prompt_template, render_prompt_template
from app.utils.json_utils import clean_json_text
from app import constants

logger = logging.getLogger(__name__)


async def parse_job_description(
    jd_text: str,
    prompt_config: Optional[Dict[str, str]] = None,
    job_type_options: Optional[list] = None,
) -> Dict[str, Any]:
    """
    AI 解析 JD 文本，提取结构化岗位信息

    Args:
        jd_text: 完整的 JD 文本

    Returns:
        解析后的结构化岗位信息
    """
    active_job_types = job_type_options or list(constants.VALID_JOB_TYPES)
    template = prompt_config or get_default_prompt_template(constants.PROMPT_KEY_JD_PARSE)
    context = {
        "job_type_options": json.dumps(active_job_types, ensure_ascii=False),
        "jd_text": jd_text,
    }
    default_template = get_default_prompt_template(constants.PROMPT_KEY_JD_PARSE)
    system_prompt = render_prompt_template(template.get("system_prompt") or default_template["system_prompt"], context)
    user_prompt = render_prompt_template(template.get("user_prompt") or default_template["user_prompt"], context)

    try:
        response = await call_deepseek(user_prompt, system_prompt)
        cleaned_response = clean_json_text(response)
        parsed_jd = json.loads(cleaned_response)

        # 新旧字段兼容
        parsed_jd["job_title"] = parsed_jd.get("job_title") or parsed_jd.get("job_name") or ""
        parsed_jd["job_name"] = parsed_jd["job_title"]
        parsed_jd["department"] = parsed_jd.get("department") or parsed_jd.get("job_type") or "未分组"
        parsed_jd["work_location"] = parsed_jd.get("work_location") or parsed_jd.get("location") or ""
        parsed_jd["location"] = parsed_jd["work_location"]
        parsed_jd["experience_requirement"] = parsed_jd.get("experience_requirement") or parsed_jd.get("experience_req") or ""
        parsed_jd["experience_req"] = parsed_jd["experience_requirement"]
        parsed_jd["education_requirement"] = parsed_jd.get("education_requirement") or parsed_jd.get("education_req") or ""
        parsed_jd["education_req"] = parsed_jd["education_requirement"]
        parsed_jd["jd_text"] = jd_text  # 保留原始 JD 文本

        # 验证岗位类型
        job_type = parsed_jd.get("job_type", "")
        if job_type not in set(active_job_types):
            parsed_jd["job_type"] = _normalize_job_type(job_type, active_job_types)

        for key in (
            "must_have_skills",
            "nice_to_have_skills",
            "responsibilities",
            "requirements",
            "key_screening_points",
            "reject_conditions",
        ):
            parsed_jd[key] = _ensure_list(parsed_jd.get(key))

        # 数字字段处理
        try:
            headcount = parsed_jd.get("headcount")
            if headcount is not None:
                parsed_jd["headcount"] = int(headcount)
            else:
                parsed_jd["headcount"] = 1
        except (ValueError, TypeError):
            parsed_jd["headcount"] = 1

        logger.info(f"JD 解析成功: job_name={parsed_jd['job_name']}")
        return parsed_jd

    except json.JSONDecodeError as e:
        logger.error(f"JD 解析 JSON 格式错误: {e}")
        raise ValueError("AI 返回的数据格式错误，请重试")
    except Exception as e:
        logger.error(f"JD 解析失败: {e}")
        raise Exception(f"JD 解析失败: {str(e)}")


def _normalize_job_type(job_type: str, job_type_options: Optional[list] = None) -> str:
    options = job_type_options or list(constants.VALID_JOB_TYPES)

    def pick(default_value: str) -> str:
        if default_value in options:
            return default_value
        return options[0] if options else constants.JOB_TYPE_GENERAL

    text = job_type or ""
    if "销售" in text or "业务" in text:
        return pick(constants.JOB_TYPE_SALES)
    if "运营" in text or "电商" in text:
        return pick(constants.JOB_TYPE_ECOMMERCE)
    if "客服" in text or "售后" in text:
        return pick(constants.JOB_TYPE_CUSTOMER_SERVICE)
    if "行政" in text or "人事" in text or "人力" in text:
        return pick(constants.JOB_TYPE_ADMIN_HR)
    if "财务" in text or "会计" in text or "出纳" in text:
        return pick(constants.JOB_TYPE_FINANCE)
    return pick(constants.JOB_TYPE_GENERAL)


def _ensure_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    if not value:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.replace("，", ",").split(",") if item.strip()]
    return [str(value)]


def build_job_update_from_parsed(parsed_jd: Dict[str, Any]) -> Dict[str, Any]:
    """
    从解析结果构建用于更新 Job 的字典

    Args:
        parsed_jd: AI 解析后的结构化 JD

    Returns:
        可用于更新 Job 模型的字典
    """
    return {
        "job_name": parsed_jd.get("job_name", ""),
        "department": parsed_jd.get("department", ""),
        "job_type": parsed_jd.get("job_type", constants.JOB_TYPE_GENERAL),
        "location": parsed_jd.get("location", ""),
        "headcount": parsed_jd.get("headcount", 1),
        "salary_range": parsed_jd.get("salary_range", ""),
        "education_req": parsed_jd.get("education_req", ""),
        "experience_req": parsed_jd.get("experience_req", ""),
        "parsed_jd_json": json.dumps(parsed_jd, ensure_ascii=False),
    }
