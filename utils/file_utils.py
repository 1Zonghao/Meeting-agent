# utils/file_utils.py
from typing import Optional
import streamlit as st

import docx2txt


def read_text_file(uploaded_file) -> Optional[str]:
    """读取 .txt 文件内容。"""
    try:
        content = uploaded_file.read()
        # 根据需要可以尝试不同编码，这里默认 utf-8
        return content.decode("utf-8", errors="ignore")
    except Exception as e:
        st.error(f"读取文本文件失败：{e}")
        return None


def read_docx_file(uploaded_file) -> Optional[str]:
    """读取 .docx 文件内容。"""
    try:
        # docx2txt 需要文件路径，这里用临时文件中转
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            text = docx2txt.process(tmp_path)
            return text
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    except Exception as e:
        st.error(f"读取 Word 文件失败：{e}")
        return None
