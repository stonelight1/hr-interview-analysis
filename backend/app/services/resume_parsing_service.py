"""
简历 AI 解析服务

支持将粘贴的完整简历文本自动解析为结构化候选人信息。
AI 不编造信息，未提供的字段返回空值。
"""
import json
import logging
from typing import Dict, Any

from app.services.deepseek_client import call_deepseek
from app.utils.json_utils import clean_json_text

logger = logging.getLogger(__name__)


async def parse_resume(resume_text: str) -> Dict[str, Any]:
    """
    AI 解析简历文本，提取结构化候选人信息

    Args:
        resume_text: 完整的简历文本

    Returns:
        解析后的结构化候选人信息
    """
    system_prompt = """你是一个专业的 HR 招聘助手。请从用户提供的简历文本中提取结构化候选人信息。

要求：
1. 只提取文本中明确写明的信息，不要编造或猜测
2. 如果某字段在简历中未提及，返回空字符串或 null
3. 必须返回严格的 JSON 格式，不要包含任何其他文字
4. 对于无法确定的信息，返回空值并在 information_gaps 中列出

请返回以下 JSON 结构：
{
    "basic_info": {
        "name": "姓名",
        "gender": "性别",
        "age": 年龄（数字）,
        "phone": "手机号",
        "email": "邮箱",
        "current_city": "当前城市",
        "expected_city": "期望城市",
        "job_search_status": "求职状态",
        "available_date": "到岗时间",
        "expected_salary": "期望薪资"
    },

    "education": {
        "highest_education": "最高学历",
        "graduation_school": "毕业学校",
        "major": "专业",
        "graduation_time": "毕业时间",
        "education_type": "学历类型（全日制/自考/成考等）"
    },

    "work_experience": [
        {
            "company_name": "公司名称",
            "industry": "所属行业",
            "position": "岗位名称",
            "start_time": "入职时间",
            "end_time": "离职时间",
            "work_years": "工作年限",
            "responsibilities": "主要职责",
            "achievements": "主要成果",
            "resignation_reason": "离职原因"
        }
    ],

    "project_experience": [
        {
            "project_name": "项目名称",
            "role": "项目角色",
            "project_time": "项目时间",
            "project_content": "项目内容",
            "responsibilities": "个人职责",
            "achievements": "项目成果"
        }
    ],

    "skills": {
        "technical_skills": "专业技能",
        "software_tools": "软件工具",
        "platform_experience": "平台经验",
        "language_ability": "语言能力",
        "certificates": "证书资质"
    },

    "ai_analysis": {
        "keywords": "简历关键词（用逗号分隔）",
        "stability_assessment": "工作稳定性判断",
        "employment_gaps": "空窗期识别",
        "job_hopping_frequency": "跳槽频率判断",
        "relevant_experience": "岗位相关经验提取",
        "highlights": "简历亮点",
        "risk_points": "简历风险点",
        "information_gaps": "信息缺失项"
    }
}"""

    user_prompt = f"""请解析以下简历文本：

{resume_text}"""

    try:
        response = await call_deepseek(user_prompt, system_prompt)
        cleaned_response = clean_json_text(response)
        parsed_resume = json.loads(cleaned_response)

        # 确保基本结构完整
        if "basic_info" not in parsed_resume:
            parsed_resume["basic_info"] = {}
        if "education" not in parsed_resume:
            parsed_resume["education"] = {}
        if "work_experience" not in parsed_resume:
            parsed_resume["work_experience"] = []
        if "project_experience" not in parsed_resume:
            parsed_resume["project_experience"] = []
        if "skills" not in parsed_resume:
            parsed_resume["skills"] = {}
        if "ai_analysis" not in parsed_resume:
            parsed_resume["ai_analysis"] = {}

        # 提取顶层字段供直接存储
        basic_info = parsed_resume["basic_info"]
        education = parsed_resume["education"]

        parsed_resume["name"] = basic_info.get("name", "")
        parsed_resume["gender"] = basic_info.get("gender", "")
        parsed_resume["phone"] = basic_info.get("phone", "")
        parsed_resume["email"] = basic_info.get("email", "")
        parsed_resume["current_city"] = basic_info.get("current_city", "")
        parsed_resume["expected_city"] = basic_info.get("expected_city", "")
        parsed_resume["job_search_status"] = basic_info.get("job_search_status", "")
        parsed_resume["available_date"] = basic_info.get("available_date", "")
        parsed_resume["expected_salary"] = basic_info.get("expected_salary", "")

        parsed_resume["education_level"] = education.get("highest_education", "")
        parsed_resume["graduation_school"] = education.get("graduation_school", "")
        parsed_resume["major"] = education.get("major", "")

        # 计算工作年限
        work_exp = parsed_resume.get("work_experience", [])
        if work_exp:
            try:
                total_years = sum(
                    float(exp.get("work_years", 0) or 0)
                    for exp in work_exp
                    if isinstance(exp.get("work_years"), (int, float, str))
                )
                parsed_resume["work_years"] = int(total_years) if total_years > 0 else None
            except (ValueError, TypeError):
                parsed_resume["work_years"] = None
        else:
            parsed_resume["work_years"] = None

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
        "phone": parsed_resume.get("phone", ""),
        "email": parsed_resume.get("email", ""),
        "current_city": parsed_resume.get("current_city", ""),
        "expected_city": parsed_resume.get("expected_city", ""),
        "job_search_status": parsed_resume.get("job_search_status", ""),
        "available_date": parsed_resume.get("available_date", ""),
        "expected_salary": parsed_resume.get("expected_salary", ""),
        "education_level": parsed_resume.get("education_level", ""),
        "graduation_school": parsed_resume.get("graduation_school", ""),
        "major": parsed_resume.get("major", ""),
        "work_years": parsed_resume.get("work_years"),
        "parsed_resume_json": json.dumps(parsed_resume, ensure_ascii=False),
    }
