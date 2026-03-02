# utils/config.py
import streamlit as st
from dataclasses import dataclass
from typing import Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


@dataclass
class ModelConfig:
    """模型配置数据类，用于集中管理 LLM / Embedding 等参数。"""
    api_key: str
    base_url: str
    model_name: str
    temperature: float
    max_tokens: int


def render_sidebar() -> Optional[ModelConfig]:
    """
    渲染 Streamlit 侧边栏，用于：
    - 输入 API Key 和 Base URL（支持 DeepSeek / 通义千问等 OpenAI 格式接口）
    - 调整模型参数（Temperature / Max Tokens）
    返回 ModelConfig；如果信息未填全，则返回 None。
    """
    with st.sidebar:
        st.title("⚙️ MeetingAgent Pro 配置")

        st.markdown("#### LLM 接口配置")
        api_key = st.text_input("API Key", type="password", key="api_key")
        base_url = st.text_input(
            "Base URL",
            value="https://dashscope.aliyuncs.com/compatible-mode/v1",
            help="可以替换为 DeepSeek / 通义千问 等兼容 OpenAI 协议的地址",
            key="base_url",
        )
        model_name = st.text_input(
            "模型名称（model name）",
            value="qwen-max",
            help="例如：gpt-4o-mini / deepseek-chat / qwen-plus 等",
            key="model_name",
        )

        st.markdown("#### 模型参数")
        temperature = st.slider(
            "Temperature (创造性程度)",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.05,
            key="temperature",
        )
        max_tokens = st.slider(
            "Max Tokens (最大输出长度)",
            min_value=256,
            max_value=4096,
            value=1024,
            step=128,
            key="max_tokens",
        )

        if not api_key:
            st.warning("请在 Sidebar 中输入 API Key 才能调用大模型。")
            return None

        return ModelConfig(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )


def get_llm(config: ModelConfig) -> ChatOpenAI:
    """
    根据 Sidebar 配置初始化 ChatOpenAI 模型。
    通过 base_url + api_key 支持 DeepSeek / 通义千问 等兼容 OpenAI 协议的模型。
    """
    llm = ChatOpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        model=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )
    return llm


def get_embeddings(config: ModelConfig) -> OpenAIEmbeddings:
    """
    初始化 Embedding 模型，用于构建向量库。
    - 这里使用 OpenAI Embeddings 接口，同样可配合自定义 Base URL 使用。
    - 实际部署时，可以将 embedding 模型名单独暴露为配置项。
    """
    embeddings = OpenAIEmbeddings(
        api_key=config.api_key,
        base_url=config.base_url,
        model="text-embedding-3-large",
    )
    return embeddings
    