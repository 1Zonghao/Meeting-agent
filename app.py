# app.py
import json
from typing import Any, Dict

import streamlit as st

from utils.config import render_sidebar, get_llm, get_embeddings
from utils.audio_utils import transcribe_audio_with_whisper, segments_to_plain_text
from utils.file_utils import read_text_file, read_docx_file
from utils.rag_utils import (
    build_or_update_vectorstore_from_uploads,
    load_vectorstore,
    retrieve_context,
    format_context_docs,
)
from utils.word_export import build_meeting_docx
from chains.meeting_agent_chain import run_meeting_agent_workflow


st.set_page_config(
    page_title="MeetingAgent Pro",
    page_icon="📝",
    layout="wide",
)


def main():
    st.title("📝 MeetingAgent Pro - 智能会议纪要助手")

    # === Sidebar 配置 ===
    config = render_sidebar()
    if config is None:
        st.stop()

    llm = get_llm(config)
    embeddings = get_embeddings(config)

    # 初始化 session_state
    if "kb_vectorstore" not in st.session_state:
        st.session_state["kb_vectorstore"] = load_vectorstore(embeddings)
    if "meeting_json" not in st.session_state:
        st.session_state["meeting_json"] = {}
    if "meeting_summary" not in st.session_state:
        st.session_state["meeting_summary"] = ""
    if "raw_meeting_text" not in st.session_state:
        st.session_state["raw_meeting_text"] = ""
    if "kb_context_text" not in st.session_state:
        st.session_state["kb_context_text"] = ""

    # === 布局：上半部分输入区，下半部分结果展示 ===
    st.markdown("### 1️⃣ 多模态输入区")

    col1, col2 = st.columns(2)

    # ---- 左侧：会议内容上传（音频 / 文本）----
    with col1:
        st.subheader("会议内容上传（音频 / 文本）")

        uploaded_meeting = st.file_uploader(
            "上传会议文件（支持 .mp3 / .wav / .txt / .docx）",
            type=["mp3", "wav", "txt", "docx"],
            key="meeting_file",
        )

        if uploaded_meeting is not None:
            filename = uploaded_meeting.name.lower()
            meeting_text = None

            try:
                if filename.endswith((".mp3", ".wav")):
                    # 音频 => Whisper 转写
                    st.info("检测到音频文件，正在调用 Whisper 进行转写...")
                    bytes_data = uploaded_meeting.read()
                    segments = transcribe_audio_with_whisper(bytes_data)
                    meeting_text = segments_to_plain_text(segments)

                elif filename.endswith(".txt"):
                    meeting_text = read_text_file(uploaded_meeting)
                elif filename.endswith(".docx"):
                    meeting_text = read_docx_file(uploaded_meeting)
                else:
                    st.error("暂不支持的文件类型。")
            except Exception as e:
                st.error(f"解析会议文件失败：{e}")

            if meeting_text:
                st.session_state["raw_meeting_text"] = meeting_text
                st.success("会议内容解析完成！可以在下方结果区查看。")

    # ---- 右侧：知识库上传区（RAG）----
    with col2:
        st.subheader("知识库上传（优秀纪要范例 / 企业背景）")

        kb_files = st.file_uploader(
            "上传用于 Few-shot 的参考资料（.txt / .docx，可多选）",
            type=["txt", "docx"],
            accept_multiple_files=True,
            key="kb_files",
        )

        if kb_files:
            if st.button("构建 / 更新知识库向量库"):
                try:
                    vectorstore = build_or_update_vectorstore_from_uploads(kb_files, embeddings)
                    if vectorstore:
                        st.session_state["kb_vectorstore"] = vectorstore
                except Exception as e:
                    st.error(f"构建向量库时出错：{e}")

        if st.session_state["kb_vectorstore"] is not None:
            st.success("已加载知识库向量库，可用于 RAG 检索。")
        else:
            st.info("尚未构建知识库向量库。建议上传一些优秀纪要样例，以便模仿风格。")

    st.markdown("---")

    # === 生成纪要按钮 ===
    st.markdown("### 2️⃣ 生成结构化会议纪要")

    if not st.session_state["raw_meeting_text"]:
        st.warning("请先上传会议内容文件（音频或文本）。")
    else:
        if st.button("🚀 一键生成会议纪要"):
            meeting_text = st.session_state["raw_meeting_text"]
            kb_context_text = ""

            # 有知识库时，先做 RAG 检索，取最相关的 3 个片段
            vectorstore = st.session_state["kb_vectorstore"]
            if vectorstore is not None:
                try:
                    docs = retrieve_context(vectorstore, meeting_text, k=3)
                    kb_context_text = format_context_docs(docs)
                    st.session_state["kb_context_text"] = kb_context_text
                except Exception as e:
                    st.error(f"RAG 检索失败，将在无知识库模式下继续：{e}")

            try:
                workflow_result = run_meeting_agent_workflow(
                    llm=llm,
                    meeting_text=meeting_text,
                    kb_context=kb_context_text,
                )
                # 优先使用 refined_json；若失败则用 extracted_json
                meeting_json = workflow_result.get("refined_json") or workflow_result.get(
                    "extracted_json"
                )
                if meeting_json is None:
                    st.warning("结构化 JSON 解析失败，请在 JSON 编辑器中手动修正。")
                    meeting_json = {}

                st.session_state["meeting_json"] = meeting_json
                st.session_state["meeting_summary"] = workflow_result.get("summary", "")

                st.success("会议纪要生成完成，请在下方标签页查看与编辑。")
            except Exception as e:
                st.error(f"调用大模型生成纪要失败：{e}")

    # === 结果展示与交互 ===
    st.markdown("### 3️⃣ 结果展示与交互")

    tab_raw, tab_structured, tab_json = st.tabs(
        ["📄 原始录音/文本", "📋 结构化纪要（Markdown）", "🧩 JSON 编辑器"]
    )

    # ---- Tab 1: 原始文本 ----
    with tab_raw:
        st.subheader("原始会议内容（文本）")
        if st.session_state["raw_meeting_text"]:
            st.text_area(
                "会议原文（只读）",
                value=st.session_state["raw_meeting_text"],
                height=350,
                key="raw_meeting_view",
            )
        else:
            st.info("尚未上传会议内容。")

    # ---- Tab 2: 结构化纪要（Markdown 表格）----
    with tab_structured:
        st.subheader("结构化会议纪要")
        meeting_json: Dict[str, Any] = st.session_state.get("meeting_json", {}) or {}

        # 议题
        topic = meeting_json.get("Topic", "（未提取）")
        st.markdown(f"**会议议题：** {topic}")

        # 关键讨论点
        key_points = meeting_json.get("KeyPoints", [])
        st.markdown("**关键讨论点：**")
        if isinstance(key_points, list) and key_points:
            for idx, kp in enumerate(key_points, start=1):
                st.markdown(f"- {idx}. {kp}")
        else:
            st.markdown("- （无）")

        # 决策结论
        decisions = meeting_json.get("Decisions", [])
        st.markdown("**决策结论：**")
        if isinstance(decisions, list) and decisions:
            for idx, dec in enumerate(decisions, start=1):
                st.markdown(f"- {idx}. {dec}")
        else:
            st.markdown("- （无）")

        # 待办事项表格（Markdown 风格）
        st.markdown("**待办事项（Action Items）：**")
        action_items = meeting_json.get("ActionItems", [])

        if isinstance(action_items, list) and action_items:
            md_lines = ["| 责任人 (Who) | 任务内容 (What) | 截止时间 (When) |", "| --- | --- | --- |"]
            for item in action_items:
                who = str(item.get("Who", ""))
                what = str(item.get("What", ""))
                when = str(item.get("When", ""))
                md_lines.append(f"| {who} | {what} | {when} |")
            st.markdown("\n".join(md_lines))
        else:
            st.markdown("> 暂无待办事项。")

        # 导出 Word
        st.markdown("---")
        st.subheader("导出为 Word 文档")
        if st.session_state["meeting_json"]:
            buffer = build_meeting_docx(
                meeting_json=st.session_state["meeting_json"],
                summary=st.session_state["meeting_summary"],
            )
            st.download_button(
                label="💾 下载 Word 纪要",
                data=buffer,
                file_name="meeting_minutes.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        else:
            st.info("生成结构化纪要后，可在此导出 Word。")

    # ---- Tab 3: JSON 编辑器 ----
    with tab_json:
        st.subheader("JSON 结果编辑器")

        meeting_json = st.session_state.get("meeting_json", {}) or {}
        json_str = json.dumps(meeting_json, ensure_ascii=False, indent=2)

        edited = st.text_area(
            "在此编辑结构化 JSON，点击下方按钮更新结果：",
            value=json_str,
            height=400,
            key="json_editor",
        )

        if st.button("保存 JSON 修改", key="save_json"):
            try:
                new_json = json.loads(edited)
                st.session_state["meeting_json"] = new_json
                st.success("JSON 已更新，结构化纪要视图和导出内容将同步刷新。")
            except Exception as e:
                st.error(f"JSON 解析失败，请检查格式是否正确：{e}")


if __name__ == "__main__":
    main()