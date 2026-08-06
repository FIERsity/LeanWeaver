"""LLM 适配器（模型层）。

设计目标（README 里的原则 3）：模型可插拔。
- 规则层（errors/）不依赖本模块
- 只有需要"理解生成"的任务（错误兜底解释、证明翻译）才走这里
- 支持双通道：云端 API（OpenAI 兼容）/ 本地 Ollama

当前实现：
- LLMBackend：统一接口（explain_error / translate_proof 为占位，待实现）
- get_default_llm：从环境变量构造默认后端（未配置 key 时返回 None）

使用：设置环境变量 LEANWEAVER_LLM_PROVIDER=openai|ollama
     以及对应 API key（OPENAI_API_KEY 或 OLLAMA_BASE_URL）。
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional


class LLMBackend(ABC):
    """LLM 后端的统一抽象。"""

    provider: str = "base"

    @abstractmethod
    def explain_error(self, message: str, code: str | None = None) -> str:
        """解释一条规则层未覆盖的 Lean 报错（返回中文解释）。"""

    @abstractmethod
    def translate_proof(self, lean_proof: str, target_lang: str = "zh") -> str:
        """把形式化证明翻译成自然语言（主线功能，待实现）。"""


class OpenAIBackend(LLMBackend):
    """OpenAI 兼容 API 后端（OpenAI / DeepSeek / 任何 OpenAI 协议网关）。"""

    provider = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        # 延迟导入：未安装 openai 包时不应破坏规则层
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "未安装 openai 包。请执行 `pip install leanweaver[llm]`。"
            )
        self._client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url or os.environ.get("OPENAI_BASE_URL"),
        )
        self._model = model or os.environ.get("LEANWEAVER_MODEL", "gpt-4o-mini")

    def explain_error(self, message: str, code: str | None = None) -> str:
        sys = (
            "你是 Lean 4 定理证明器的中文导师。用户会给你一条英文报错。"
            "请用通俗中文解释：1) 这个错误是什么意思 2) 常见原因 3) 修复建议。"
            "语言要平实，面向数学/编程背景的初学者。"
        )
        user = f"Lean 报错：\n{message}"
        if code:
            user += f"\n\n出错代码：\n{code}"
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or "（模型返回为空）"

    def translate_proof(self, lean_proof: str, target_lang: str = "zh") -> str:
        raise NotImplementedError("证明翻译器主线功能开发中（roadmap 阶段 ②）")


class OllamaBackend(LLMBackend):
    """本地 Ollama 后端（免费、离线、隐私优先）。"""

    provider = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self._base_url = base_url or os.environ.get(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        self._model = model or os.environ.get("LEANWEAVER_MODEL", "qwen2.5-coder:7b")

    def explain_error(self, message: str, code: str | None = None) -> str:
        # Ollama 原生 HTTP API，无需额外依赖
        import json
        import urllib.request

        sys = (
            "你是 Lean 4 定理证明器的中文导师。用通俗中文解释下面的 Lean 报错："
            "1) 意思 2) 常见原因 3) 修复建议。"
        )
        user = f"Lean 报错：\n{message}"
        if code:
            user += f"\n\n出错代码：\n{code}"
        payload = json.dumps(
            {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": sys},
                    {"role": "user", "content": user},
                ],
                "stream": False,
            }
        ).encode()
        req = urllib.request.Request(
            f"{self._base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        return data.get("message", {}).get("content", "（模型返回为空）")

    def translate_proof(self, lean_proof: str, target_lang: str = "zh") -> str:
        raise NotImplementedError("证明翻译器主线功能开发中（roadmap 阶段 ②）")


def get_default_llm() -> Optional[LLMBackend]:
    """根据环境变量构造默认 LLM 后端。

    未配置任何凭证时返回 None（规则层可正常离线工作）。
    """
    provider = os.environ.get("LEANWEAVER_LLM_PROVIDER", "").lower()
    if provider == "ollama":
        return OllamaBackend()
    if provider in ("openai", "deepseek", "azure", ""):
        if os.environ.get("OPENAI_API_KEY"):
            return OpenAIBackend()
    return None
