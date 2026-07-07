"""
简历 AI 解析服务

支持将粘贴的完整简历文本自动解析为结构化候选人信息。
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


async def parse_resume(
    resume_text: str,
    prompt_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    AI 解析简历文本，提取结构化候选人信息

    Args:
        resume_text: 完整的简历文本

    Returns:
        解析后的结构化候选人信息
    """
    template = prompt_config or get_default_prompt_template(constants.PROMPT_KEY_RESUME_PARSE)
    default_template = get_default_prompt_template(constants.PROMPT_KEY_RESUME_PARSE)
    context = {"resume_text": resume_text}
    system_prompt = render_prompt_template(template.get("system_prompt") or default_template["system_prompt"], context)
    user_prompt = render_prompt_template(template.get("user_prompt") or default_template["user_prompt"], context)

    try:
        response = await call_deepseek(user_prompt, system_prompt)
        cleaned_response = clean_json_text(response)
        parsed_resume = json.loads(cleaned_response)

        parsed_resume = normalize_parsed_resume(parsed_resume)

        # 保留原始简历文本
        parsed_resume["resume_text"] = resume_text

        logger.info(f"简历解析成功: name={parsed_resume.get('name', '未知')}")
        return parsed_resume

    except json.JSONDecodeError as e:
        logger.error(f"简历解析 JSON 格式错误: {e}")
        raise ValueError("AI 返回的数据格式错误，请重试")
    except Exception as e:
        logger.error(f"简历解析失败: {e}")
        raise Exception(f"简历解析失败: {str(e)}")


def build_candidate_update_from_parsed(parsed_resume: Dict[str, Any]) -> Dict[str, Any]:
    """
    从解析结果构建用于更新 Candidate 的字典

    Args:
        parsed_resume: AI 解析后的结构化简历

    Returns:
        可用于更新 Candidate 模型的字典
    """
    return {
        "candidate_name": parsed_resume.get("name", ""),
        "gender": parsed_resume.get("gender", ""),
        "age": _parse_int_or_none(parsed_resume.get("age")),
        "phone": parsed_resume.get("phone", ""),
        "email": parsed_resume.get("email", ""),
        "current_city": parsed_resume.get("city", "") or parsed_resume.get("current_city", ""),
        "expected_city": parsed_resume.get("expected_city", ""),
        "job_search_status": parsed_resume.get("job_search_status", ""),
        "available_date": parsed_resume.get("available_time", "") or parsed_resume.get("available_date", ""),
        "expected_salary": parsed_resume.get("salary_expectation", "") or parsed_resume.get("expected_salary", ""),
        "education_level": parsed_resume.get("education", "") or parsed_resume.get("education_level", ""),
        "graduation_school": parsed_resume.get("school", "") or parsed_resume.get("graduation_school", ""),
        "major": parsed_resume.get("major", ""),
        "work_years": _parse_int_or_none(parsed_resume.get("work_years")),
        "parsed_resume_json": json.dumps(parsed_resume, ensure_ascii=False),
    }


def normalize_parsed_resume(parsed_resume: Dict[str, Any]) -> Dict[str, Any]:
    """兼容新旧简历解析 JSON，并补齐工作台需要的顶层字段。"""
    basic_info = parsed_resume.get("basic_info") if isinstance(parsed_resume.get("basic_info"), dict) else {}
    education_info = parsed_resume.get("education") if isinstance(parsed_resume.get("education"), dict) else {}
    ai_analysis = parsed_resume.get("ai_analysis") if isinstance(parsed_resume.get("ai_analysis"), dict) else {}

    work_experience = parsed_resume.get("work_experience")
    if not isinstance(work_experience, list):
        work_experience = []

    project_experience = parsed_resume.get("project_experience")
    if not isinstance(project_experience, list):
        project_experience = []

    skills = parsed_resume.get("skills")
    if isinstance(skills, dict):
        skills_list = [
            str(value).strip()
            for value in skills.values()
            if str(value or "").strip()
        ]
    elif isinstance(skills, list):
        skills_list = [str(item).strip() for item in skills if str(item or "").strip()]
    elif skills:
        skills_list = [str(skills)]
    else:
        skills_list = []

    latest = work_experience[0] if work_experience and isinstance(work_experience[0], dict) else {}
    past_companies = []
    for exp in work_experience:
        if isinstance(exp, dict) and exp.get("company_name"):
            past_companies.append(exp.get("company_name"))

    normalized = {
        "name": parsed_resume.get("name") or basic_info.get("name") or "",
        "phone": parsed_resume.get("phone") or basic_info.get("phone") or "",
        "email": parsed_resume.get("email") or basic_info.get("email") or "",
        "gender": parsed_resume.get("gender") or basic_info.get("gender") or "",
        "age": parsed_resume.get("age") or basic_info.get("age") or "",
        "city": parsed_resume.get("city") or parsed_resume.get("current_city") or basic_info.get("current_city") or "",
        "current_city": parsed_resume.get("current_city") or parsed_resume.get("city") or basic_info.get("current_city") or "",
        "expected_city": parsed_resume.get("expected_city") or basic_info.get("expected_city") or "",
        "education": parsed_resume.get("education") if isinstance(parsed_resume.get("education"), str) else education_info.get("highest_education", ""),
        "education_level": parsed_resume.get("education_level") or education_info.get("highest_education") or "",
        "school": parsed_resume.get("school") or education_info.get("graduation_school") or "",
        "graduation_school": parsed_resume.get("graduation_school") or parsed_resume.get("school") or education_info.get("graduation_school") or "",
        "major": parsed_resume.get("major") or education_info.get("major") or "",
        "graduation_year": parsed_resume.get("graduation_year") or education_info.get("graduation_time") or "",
        "work_years": parsed_resume.get("work_years") or _derive_work_years(work_experience) or "",
        "latest_company": parsed_resume.get("latest_company") or latest.get("company_name") or "",
        "latest_position": parsed_resume.get("latest_position") or latest.get("position") or "",
        "past_companies": parsed_resume.get("past_companies") if isinstance(parsed_resume.get("past_companies"), list) else past_companies,
        "skills": skills_list,
        "work_experience": work_experience,
        "project_experience": project_experience,
        "industry_experience": parsed_resume.get("industry_experience") or ai_analysis.get("relevant_experience") or "",
        "salary_expectation": parsed_resume.get("salary_expectation") or basic_info.get("expected_salary") or parsed_resume.get("expected_salary") or "",
        "expected_salary": parsed_resume.get("expected_salary") or parsed_resume.get("salary_expectation") or basic_info.get("expected_salary") or "",
        "available_time": parsed_resume.get("available_time") or basic_info.get("available_date") or parsed_resume.get("available_date") or "",
        "available_date": parsed_resume.get("available_date") or parsed_resume.get("available_time") or basic_info.get("available_date") or "",
        "raw_resume_summary": parsed_resume.get("raw_resume_summary") or ai_analysis.get("highlights") or "",
        "missing_fields": parsed_resume.get("missing_fields") if isinstance(parsed_resume.get("missing_fields"), list) else _normalize_gap_list(ai_analysis.get("information_gaps")),
        "job_search_status": parsed_resume.get("job_search_status") or basic_info.get("job_search_status") or "",
    }

    parsed_resume.update(normalized)
    return parsed_resume


def _derive_work_years(work_experience: list) -> str:
    values = []
    for exp in work_experience:
        if isinstance(exp, dict) and exp.get("work_years") not in (None, ""):
            values.append(str(exp.get("work_years")))
    return "，".join(values)


def _normalize_gap_list(value: Any) -> list:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if isinstance(value, str) and value.strip():
        return [item.strip() for item in value.replace("，", ",").split(",") if item.strip()]
    return []


def _parse_int_or_none(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).replace("年", "").strip()))
    except (TypeError, ValueError):
        return None
