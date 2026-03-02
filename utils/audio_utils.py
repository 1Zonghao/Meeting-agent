# utils/audio_utils.py
import io
from typing import List, Dict

import streamlit as st

# Whisper 可选依赖：
# - 默认尝试导入，如果未安装 openai-whisper，则退回到 Mock 逻辑。
try:
    import whisper  # openai-whisper 库
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# 如果你当前开发环境没有正确安装 ffmpeg，希望始终走 Mock 转写，
# 可以手动把下面这一行取消注释，强制关闭 Whisper：
# WHISPER_AVAILABLE = False

def transcribe_audio_with_whisper(file_bytes: bytes, model_name: str = "small") -> List[Dict]:
    """
    使用 Whisper 模型进行音频转写，返回带时间戳的片段列表。
    返回格式示例：
    [
        {"start": 0.0, "end": 3.5, "text": "大家好，欢迎参加今天的项目会议。"},
        ...
    ]
    """
    if not WHISPER_AVAILABLE:
        # === Mock 逻辑 ===
        # 在本地/教学环境中，如果无法安装或运行 Whisper，
        # 使用简单的 Mock 实现，返回伪造的时间戳文本，方便前端联调。
        # 实际部署时，应安装 openai-whisper，并删除此分支。
        st.info("当前环境未安装 Whisper，将使用 Mock 转写结果（示例数据）。")
        return [
            {"start": 0.0, "end": 5.0, "text": "【Mock】大家好，欢迎参加今天的项目会议。"},
            {"start": 5.0, "end": 15.0, "text": "【Mock】本次会议主要讨论项目进度和任务分工。"},
        ]

    # === 真正的 Whisper 推理逻辑 ===
    # Whisper 期望读的是一个文件路径或 numpy 数组；这里用临时文件的方式。
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(tmp_path, task="transcribe", verbose=False)
        segments = []
        for seg in result.get("segments", []):
            segments.append(
                {
                    "start": float(seg.get("start", 0.0)),
                    "end": float(seg.get("end", 0.0)),
                    "text": seg.get("text", "").strip(),
                }
            )
        return segments
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def segments_to_plain_text(segments: List[Dict]) -> str:
    """
    将带时间戳的 Whisper 片段合并为纯文本。
    同时保留简单的时间标记，方便调试和查看。
    """
    lines = []
    for seg in segments:
        start = seg["start"]
        end = seg["end"]
        text = seg["text"]
        lines.append(f"[{start:.1f}s - {end:.1f}s] {text}")
    return "\n".join(lines)
    