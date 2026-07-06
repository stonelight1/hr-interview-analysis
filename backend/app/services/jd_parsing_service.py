"""
JD AI 解析服务

支持将粘贴的完整 JD 文本自动解析为结构化岗位信息。
AI 不编造信息，未提供的字段返回空值。
"""
import json
import logging
from typing import Dict, Any

from app.services.deepseek_client import call_deepseek
from app.utils.json_utils import clean_json_text
from app import constants

logger = logging.getLogger(__name__)


async def parse_job_description(jd_text: str) -> Dict[str, Any]:
    """
    AI 解析 JD 文本，提取结构化岗位信息

    Args:
        jd_text: 完整的 JD 文本

    Returns:
        解析后的结构化岗位信息
    """
    system_prompt = f"""你是一个专业的 HR 招聘助手。请从用户提供的 JD（职位描述）文本中提取结构化岗位信息。

要求：
1. 只提取文本中明确写明的信息，不要编造或猜测
2. 如果某字段在 JD 中未提及，返回空字符串或 null
3. 必须返回严格的 JSON 格式，不要包含任何其他文字

岗位类型选项（请根据 JD 内容判断最合适的类型）：
{json.dumps(list(constants.VALID_JOB_TYPES), ensure_ascii=False)}

请返回以下 JSON 结构：
{{
    "job_name": "岗位名称",
    "department": "所属部门",
    "job_type": "岗位类型（从选项中选择最合适的）",
    "location": "工作地点",
    "headcount": 招聘人数（数字）,
    "salary_range": "薪资范围",
    "work_nature": "工作性质（全职/兼职）",
    "work_time": "工作时间",
    "report_to": "汇报对象",

    "education_req": "学历要求",
    "age_req": "年龄要求",
    "experience_req": "工作年限要求",
    "industry_exp_req": "行业经验要求",
    "position_exp_req": "岗位经验要求",
    "major_req": "专业要求",
    "certificate_req": "证书要求",
    "skill_req": "技能要求",
    "software_req": "软件工具要求",
    "personality_req": "性格特质要求",
    "stability_req": "稳定性要求",

    "core_responsibilities": "核心职责",
    "daily_work": "日常工作内容",
    "key_tasks": "关键任务",
    "collaboration_departments": "需要协作的部门",
    "performance_requirements": "绩效或结果要求",

    "must_have_conditions": "必须满足条件",
    "nice_to_have_conditions": "加分条件",
    "flexible_conditions": "可放宽条件",
    "deal_breakers": "明确不合适条件",
    "interview_focus": "面试重点关注项",

    "keywords": "岗位关键词（用逗号分隔）",
    "resume_screening_dimensions": "建议简历筛选维度",
    "interview_questions": "建议初试追问问题",
    "risk_points": "常见风险判断点"
}}"""

    user_prompt = f"""请解析以下 JD 文本：

{jd_text}"""

    try:
        response = await call_deepseek(user_prompt, system_prompt)
        cleaned_response = clean_json_text(response)
        parsed_jd = json.loads(cleaned_response)

        # 确保必填字段有值
        parsed_jd["job_name"] = parsed_jd.get("job_name") or ""
        parsed_jd["department"] = parsed_jd.get("department") or ""
        parsed_jd["jd_text"] = jd_text  # 保留原始 JD 文本

        # 验证岗位类型
        job_type = parsed_jd.get("job_type", "")
        if job_type not in constants.VALID_JOB_TYPES:
            parsed_jd["job_type"] = constants.JOB_TYPE_GENERAL

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
