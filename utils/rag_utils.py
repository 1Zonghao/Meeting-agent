# utils/rag_utils.py
from typing import List, Optional
import os

import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from .file_utils import read_text_file, read_docx_file


# === RAG 架构设计思路（简述）===
# 1. 用户上传“优秀纪要样例 / 企业背景资料” => 解析为原始长文本。
# 2. 使用 RecursiveCharacterTextSplitter 将长文本切分为重叠的短 chunk，
#    以减少“语义碎片化”问题，并保留局部上下文。
# 3. 将每个 chunk 包装为 LangChain 的 Document，对其内容做 Embedding，
#    存入本地向量库（这里选用 FAISS），并可将索引持久化到 storage/vectorstores。
# 4. 生成会议纪要时，用“会议全文 + 提示语”作为 query，
#    在向量库中检索最相似的若干 chunk（例如 k=3），作为风格/背景 Few-shot Context，
#    拼接到提示中，使 LLM 更好地对齐企业话术风格和纪要结构。


VECTOR_DIR = "storage/vectorstores"
VECTOR_INDEX_NAME = "meeting_examples"


def ensure_vector_dir():
    os.makedirs(VECTOR_DIR, exist_ok=True)


def build_or_update_vectorstore_from_uploads(
    uploaded_files,
    embeddings: OpenAIEmbeddings,
) -> Optional[FAISS]:
    """
    从上传的“纪要范例 / 企业资料”构建或更新 FAISS 向量库。
    - 对每个文件解析文本，切分为 Document chunk，再写入向量库。
    - 返回内存中的 FAISS 对象，同时保存到本地目录，方便下次加载。
    """
    docs: List[Document] = []

    for f in uploaded_files:
        name = f.name.lower()
        text = None

        if name.endswith(".txt"):
            text = read_text_file(f)
        elif name.endswith(".docx"):
            text = read_docx_file(f)
        else:
            st.warning(f"暂不支持的知识库文件格式：{name}（仅支持 .txt / .docx）")

        if not text:
            continue

        # 将每个文件的文本切分为 chunk
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""],
        )
        chunks = splitter.split_text(text)
        file_docs = [
            Document(
                page_content=chunk,
                metadata={"source": name},
            )
            for chunk in chunks
        ]
        docs.extend(file_docs)

    if not docs:
        st.error("没有成功解析的知识库文件，无法构建向量库。")
        return None

    ensure_vector_dir()

    with st.spinner("正在构建本地向量库（FAISS）..."):
        vectorstore = FAISS.from_documents(docs, embeddings)
        # 本地持久化，方便下次直接加载
        vectorstore.save_local(os.path.join(VECTOR_DIR, VECTOR_INDEX_NAME))

    st.success("知识库向量化完成，可用于 RAG 检索。")
    return vectorstore


def load_vectorstore(embeddings: OpenAIEmbeddings) -> Optional[FAISS]:
    """从本地加载已保存的向量库，如果不存在则返回 None。"""
    ensure_vector_dir()
    path = os.path.join(VECTOR_DIR, VECTOR_INDEX_NAME)
    if not os.path.exists(path):
        return None

    try:
        vectorstore = FAISS.load_local(
            path,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        return vectorstore
    except Exception as e:
        st.error(f"加载本地向量库失败：{e}")
        return None


def retrieve_context(
    vectorstore: FAISS,
    query: str,
    k: int = 3,
) -> List[Document]:
    """
    从向量库中检索与当前会议内容最相关的 k 个样例片段。
    这些片段会作为 Few-shot Context 传给 LLM。
    """
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    docs = retriever.get_relevant_documents(query)
    return docs


def format_context_docs(docs: List[Document]) -> str:
    """
    将检索到的 Document 列表拼接为文本，供提示词使用。
    """
    lines = []
    for idx, d in enumerate(docs, start=1):
        source = d.metadata.get("source", "unknown")
        lines.append(f"【示例片段 {idx} | 来源: {source}】\n{d.page_content}\n")
    return "\n\n".join(lines)