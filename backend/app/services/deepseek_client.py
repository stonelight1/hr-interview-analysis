import json
import httpx
from app.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """你是一名专业 HR 面试分析助手，擅长根据岗位 JD、候选人简历、面试记录，分析候选人与岗位的匹配度、优势、不足、风险点，并复盘 HR 的面试表现。

业务背景：
- 公司是电商公司。
- 业务是美的净水器经销商。
- 常见岗位包括电商客服、售后客服、销售、运营助理、仓库、文员、财务、人事行政等。
- 大部分面试是初面。
- 分析报告主要给 HR 自己看，也需要生成一段可以给领导看的简短结论。

你的任务：
1. 分析候选人是否匹配应聘岗位。
2. 核对简历声称的经历、技能和岗位要求是否被面试回答验证。
3. 分析候选人的优势、不足、风险点。
4. 给出下一轮建议追问问题。
5. 复盘 HR 本次面试表现。
6. 检查 HR 是否遗漏关键问题。
7. 检查面试中是否存在不合规或敏感问题。
8. 输出严格 JSON。

评分模型：
- 简历只代表候选人声称的经历，不等同于已验证能力。
- 综合分必须以面试验证为核心，简历匹配不能掩盖糟糕面试表现。
- score_detail.job_experience_match：岗位核心能力验证，满分 35。
- score_detail.industry_product_match：简历真实性/经历一致性，满分 20。
- score_detail.communication_ability：问题解决与案例深度，满分 20。
- score_detail.stability_motivation：沟通表达与稳定性，满分 10。
- score_detail.salary_arrival_match：薪资/到岗匹配，满分 10。
- score_detail.risk_control：风险控制，满分 5。
- match_score 应等于上述维度分之和，但后端会再次复核并执行封顶。

面试验证状态：
- VERIFIED：简历声称或岗位能力已被面试回答有效证明。
- PARTIAL：有一些证据，但案例、过程或结果不完整。
- MISSING：岗位核心能力缺少证据。
- CONTRADICTED：简历声称与面试回答矛盾，或候选人无法解释关键经历。
- UNVERIFIED：简历提到但 HR 没问到，不能按已验证能力加高分。

封顶原则：
- 面试记录无有效回答、全是数字或大量无意义内容，最终分不能高于 35。
- 简历关键经历与面试明显矛盾，最终分不能高于 45。
- 核心岗位能力缺少面试证据，最终分不能高于 50。
- 核心简历声称未被面试验证，最终分不能高于 60。
- 触发封顶时，recommendation 不得给“建议进入下一轮”或“强烈建议进入下一轮”。

重要要求：
- 必须基于输入内容分析，不要凭空编造。
- 如果信息不足，要明确写"信息不足"。
- 不要因为候选人表达积极就直接给高分，要看证据。
- 不要输出 Markdown。
- 不要输出代码块。
- 不要输出解释文字。
- 只能输出 JSON。
- 所有字段必须存在。
- 所有数组字段没有内容时返回空数组。
- 分数必须是整数。
- match_score 范围是 0 到 100。
- recommendation 只能是：强烈建议进入下一轮、建议进入下一轮、暂缓、不建议。
- risk_level 只能是：低、中、高。
- confidence 只能是：低、中、高。
- leader_summary.decision 只能是：可复试、待观察、不推荐。

合规要求：
- 不要基于性别、年龄、婚育、疾病、地域、民族等敏感因素做歧视性判断。
- 如果面试记录中 HR 问了婚育、疾病、家庭、隐私等敏感问题，需要在 compliance_risks 中指出。
- 如果未发现明显合规风险，返回"无明显不合规问题"。"""

USER_PROMPT_TEMPLATE = """请根据以下信息生成 HR 面试分析报告。

【候选人姓名】
{candidate_name}

【应聘岗位】
{job_title}

【岗位 JD / 岗位要求】
{jd_text}

【候选人简历文本】
{resume_text}

【面试记录文本】
{interview_text}

请严格返回以下 JSON 结构，字段必须完整，不能新增字段，不能缺字段：

{{
  "candidate_overview": {{
    "candidate_name": "",
    "job_title": "",
    "summary": "",
    "match_score": 0,
    "recommendation": "",
    "risk_level": "",
    "confidence": ""
  }},
  "score_detail": {{
    "job_experience_match": {{
      "score": 0,
      "max_score": 35,
      "reason": ""
    }},
    "industry_product_match": {{
      "score": 0,
      "max_score": 20,
      "reason": ""
    }},
    "communication_ability": {{
      "score": 0,
      "max_score": 20,
      "reason": ""
    }},
    "stability_motivation": {{
      "score": 0,
      "max_score": 10,
      "reason": ""
    }},
    "salary_arrival_match": {{
      "score": 0,
      "max_score": 10,
      "reason": ""
    }},
    "risk_control": {{
      "score": 0,
      "max_score": 5,
      "reason": ""
    }}
  }},
  "interview_verification": [
    {{
      "claim": "简历或岗位中的关键能力/经历",
      "interview_evidence": "面试中支持或否定该能力的具体回答；没有证据时写信息不足",
      "status": "VERIFIED/PARTIAL/MISSING/CONTRADICTED/UNVERIFIED",
      "is_core": true,
      "score_impact": "该验证状态对评分和建议的影响"
    }}
  ],
  "scoring_model": {{
    "version": "interview_verification_v1",
    "paper_score": 0,
    "interview_verification_score": 0,
    "risk_control_score": 0,
    "applied_caps": []
  }},
  "candidate_analysis": {{
    "advantages": [
      {{
        "title": "",
        "detail": "",
        "evidence": ""
      }}
    ],
    "weaknesses": [
      {{
        "title": "",
        "detail": "",
        "evidence": ""
      }}
    ],
    "risk_points": [
      {{
        "risk": "",
        "level": "",
        "detail": ""
      }}
    ]
  }},
  "follow_up_questions": [
    {{
      "question": "",
      "purpose": ""
    }}
  ],
  "hr_interview_feedback": {{
    "overall_comment": "",
    "strengths": [],
    "improvements": [],
    "missed_questions": [],
    "compliance_risks": [
      {{
        "risk": "",
        "detail": ""
      }}
    ]
  }},
  "leader_summary": {{
    "short_conclusion": "",
    "decision": ""
  }}
}}"""


def build_user_prompt(candidate_name: str, job_title: str, jd_text: str,
                      resume_text: str, interview_text: str) -> str:
    return USER_PROMPT_TEMPLATE.format(
        candidate_name=candidate_name,
        job_title=job_title,
        jd_text=jd_text,
        resume_text=resume_text,
        interview_text=interview_text
    )


async def call_deepseek(user_prompt: str, system_prompt: str = None) -> str:
    settings = get_settings()

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    else:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4000
    }

    async with httpx.AsyncClient(timeout=120.0, proxy=None) as client:
        response = await client.post(
            f"{settings.deepseek_base_url}/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
