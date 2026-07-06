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
2. 分析候选人的优势、不足、风险点。
3. 给出下一轮建议追问问题。
4. 复盘 HR 本次面试表现。
5. 检查 HR 是否遗漏关键问题。
6. 检查面试中是否存在不合规或敏感问题。
7. 输出严格 JSON。

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
      "max_score": 25,
      "reason": ""
    }},
    "industry_product_match": {{
      "score": 0,
      "max_score": 15,
      "reason": ""
    }},
    "communication_ability": {{
      "score": 0,
      "max_score": 20,
      "reason": ""
    }},
    "stability_motivation": {{
      "score": 0,
      "max_score": 20,
      "reason": ""
    }},
    "salary_arrival_match": {{
      "score": 0,
      "max_score": 10,
      "reason": ""
    }},
    "risk_control": {{
      "score": 0,
      "max_score": 10,
      "reason": ""
    }}
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
