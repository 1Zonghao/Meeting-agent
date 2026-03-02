# chains/meeting_agent_chain.py
from typing import Dict, Any, Optional, Tuple

import json
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


SUMMARY_PROMPT = ChatPromptTemplate.from_template(
    """
你是一名专业的中文会议纪要助手，请根据【会议全文】和【参考示例】生成简明扼要的会议摘要。

【参考示例，可为空】
{kb_context}

【会议全文】
{meeting_text}

请用中文总结本次会议的核心内容，长度控制在 200~400 字之间。
"""
)

EXTRACTION_PROMPT = ChatPromptTemplate.from_template(
    """
你是一名专业的结构化信息抽取助手。请从以下【会议全文】中提取结构化纪要信息，
并严格按照指定 JSON Schema 返回。

【参考示例，可为空】
{kb_context}

【会议全文】
{meeting_text}

请你返回一个 JSON，对应的 Schema 为：
{{
  "Topic": "string, 会议的主要议题/主题，简短一句话",
  "KeyPoints": ["string, 关键讨论点，按要点列出"],
  "Decisions": ["string, 会议过程中形成的明确决策"],
  "ActionItems": [
    {{
      "Who": "string, 责任人姓名或角色",
      "What": "string, 需要完成的具体事项",
      "When": "string, 预期完成时间，若未提及请填 '未明确'"
    }}
  ]
}}

要求：
1. 直接返回 JSON，不要添加任何额外说明文字。
2. 若某一项为空，请使用合理的空值（例如 [] 或 ""），不要省略字段。
"""
)

REFINEMENT_PROMPT = ChatPromptTemplate.from_template(
    """
你是一名严格的质检员，负责检查会议纪要是否遗漏要点。

【会议全文】
{meeting_text}

【当前摘要】
{summary}

【当前结构化纪要 JSON】
{structured_json}

【参考示例，可为空】
{kb_context}

请你执行以下任务：
1. 检查摘要和结构化纪要是否覆盖了会议全文中的所有重要信息（特别是决策和待办事项）。
2. 如有遗漏，请在保留原有结构的基础上，**补充**缺失的信息。
3. 最终仍然以相同 Schema 输出一个 JSON，对原有内容进行修订/补充。

注意：
- 只输出 JSON，不要多余解释。
"""
)


def _call_llm_for_summary(
    llm: ChatOpenAI,
    meeting_text: str,
    kb_context: str,
) -> str:
    """Summary Node：调用 LLM 生成会议摘要。"""
    chain = SUMMARY_PROMPT | llm
    resp = chain.invoke({"meeting_text": meeting_text, "kb_context": kb_context})
    return resp.content.strip()


def _call_llm_for_extraction(
    llm: ChatOpenAI,
    meeting_text: str,
    kb_context: str,
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Extraction Node：调用 LLM 抽取结构化 JSON。
    返回 (parsed_json, raw_text)，方便前端展示 & 编辑。
    """
    chain = EXTRACTION_PROMPT | llm
    resp = chain.invoke({"meeting_text": meeting_text, "kb_context": kb_context})
    raw = resp.content.strip()

    try:
        data = json.loads(raw)
        return data, raw
    except Exception:
        # 解析失败时，返回 None + 原始文本，方便用户手动修正
        return None, raw


def _call_llm_for_refinement(
    llm: ChatOpenAI,
    meeting_text: str,
    kb_context: str,
    summary: str,
    structured_json: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Refinement Node：检查并补充 JSON 内容。
    """
    chain = REFINEMENT_PROMPT | llm
    raw_input_json = json.dumps(structured_json, ensure_ascii=False, indent=2)
    resp = chain.invoke(
        {
            "meeting_text": meeting_text,
            "kb_context": kb_context,
            "summary": summary,
            "structured_json": raw_input_json,
        }
    )
    raw = resp.content.strip()

    try:
        refined = json.loads(raw)
        return refined, raw
    except Exception:
        # 若 refinement 阶段解析失败，保留原始 structured_json
        return None, raw


def run_meeting_agent_workflow(
    llm: ChatOpenAI,
    meeting_text: str,
    kb_context: str = "",
) -> Dict[str, Any]:
    """
    智能体工作流入口函数，按顺序执行：
    1. Summary Node：生成摘要
    2. Extraction Node：提取结构化 JSON
    3. Refinement Node：基于全文 & 示例，检查并补充结构化 JSON

    返回 dict，包含：
    - summary
    - extracted_json (原始抽取结果，可能为 None)
    - extracted_raw (原始 LLM 文本)
    - refined_json (修订后的 JSON，可能为 None)
    - refined_raw (修订阶段的原始 LLM 文本)
    """
    result: Dict[str, Any] = {}

    with st.spinner("正在生成会议摘要..."):
        summary = _call_llm_for_summary(llm, meeting_text, kb_context)
    result["summary"] = summary

    with st.spinner("正在抽取结构化纪要 JSON..."):
        extracted_json, extracted_raw = _call_llm_for_extraction(llm, meeting_text, kb_context)
    result["extracted_json"] = extracted_json
    result["extracted_raw"] = extracted_raw

    if extracted_json is None:
        st.warning("初次抽取的 JSON 无法解析，请在 JSON 编辑器中手动修正后再进行优化。")
        result["refined_json"] = None
        result["refined_raw"] = ""
        return result

    with st.spinner("正在进行纪要内容完善与补充..."):
        refined_json, refined_raw = _call_llm_for_refinement(
            llm, meeting_text, kb_context, summary, extracted_json
        )

    result["refined_json"] = refined_json
    result["refined_raw"] = refined_raw

    return result