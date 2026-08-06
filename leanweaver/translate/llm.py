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
from pathlib import Path
from typing import Optional


# 项目根目录（leanweaver/ 的上一级）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_dotenv(path: Path | None = None) -> None:
    """轻量 .env 加载：把 KEY=VALUE 写入环境变量（不覆盖已存在的）。"""
    dotenv_path = path or (_PROJECT_ROOT / ".env")
    if not dotenv_path.exists():
        return
    try:
        for line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        pass


# 模块加载时自动读取 .env（幂等）
_load_dotenv()


# 支持的采样参数（参考 OpenAI SDK / litellm 通用写法）
# 值 None 表示使用 provider 默认
SUPPORTED_PARAMS = [
    "temperature",
    "max_tokens",
    "top_p",
    "presence_penalty",
    "frequency_penalty",
    "stop",
    "seed",
    "timeout",
]

# 从环境变量读取采样参数默认值（如 LEANWEAVER_TEMPERATURE=0.3）
def _env_sampling_params() -> dict:
    out = {}
    for p in SUPPORTED_PARAMS:
        env_key = f"LEANWEAVER_{p.upper()}"
        val = os.environ.get(env_key)
        if val is None:
            continue
        try:
            if p == "max_tokens":
                out[p] = int(val)
            elif p == "stop":
                out[p] = [s.strip() for s in val.split("|") if s.strip()]
            elif p == "timeout":
                out[p] = float(val)
            else:
                out[p] = float(val)
        except ValueError:
            pass
    return out


class LLMBackend(ABC):
    """LLM 后端的统一抽象。"""

    provider: str = "base"
    # 采样参数默认值（可被调用方 kwargs 覆盖）
    sampling: dict = {}

    @abstractmethod
    def complete(self, system: str, user: str, **kwargs) -> str:
        """通用对话补全（system + user → 回复）。kwargs 可含采样参数。"""

    @abstractmethod
    def explain_error(self, message: str, code: str | None = None, lang: str = "en") -> str:
        """解释一条规则层未覆盖的 Lean 报错（返回指定语言的解释）。"""

    @abstractmethod
    def translate_proof(self, lean_proof: str, target_lang: str = "zh") -> str:
        """把形式化证明翻译成自然语言（主线功能）。"""


class OpenAIBackend(LLMBackend):
    """OpenAI 兼容 API 后端（OpenAI / DeepSeek / 任何 OpenAI 协议网关）。"""

    provider = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        sampling: dict | None = None,
    ):
        # 延迟导入：未安装 openai 包时不应破坏规则层
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "未安装 openai 包。请执行 `pip install leanweaver[llm]`。"
            )
        # 系统代理可能配置异常（如 NO_PROXY 含非法 IPv6 项 `[::1]`）导致 httpx 崩溃。
        # 在干净环境中构建 client：临时清掉代理变量，绕开坏配置。
        saved = {k: os.environ.get(k) for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY")}
        for k in saved:
            os.environ.pop(k, None)
        try:
            self._client = OpenAI(
                api_key=api_key or os.environ.get("OPENAI_API_KEY"),
                base_url=base_url or os.environ.get("OPENAI_BASE_URL"),
            )
        finally:
            # 恢复代理变量（仅恢复存在过的）
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v
        self._model = model or os.environ.get("LEANWEAVER_MODEL", "gpt-4o-mini")
        # 采样参数：显式传入 > 环境变量 > 默认
        self.sampling = _env_sampling_params()
        if sampling:
            self.sampling.update(sampling)

    def complete(self, system: str, user: str, **kwargs) -> str:
        # 合并采样参数：调用方 kwargs > 实例默认（来自 env/构造）> provider 默认
        params = dict(self.sampling)
        for k in SUPPORTED_PARAMS:
            if k in kwargs:
                params[k] = kwargs[k]
        params.pop("timeout", None)  # timeout 单独处理

        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            timeout=kwargs.get("timeout", 120),
            **params,
        )
        return resp.choices[0].message.content or ""

    def explain_error(self, message: str, code: str | None = None, lang: str = "en") -> str:
        if lang == "zh":
            sys = (
                "你是 Lean 4 定理证明器的中文导师。用户会给你一条英文报错。"
                "请用通俗中文解释：1) 这个错误是什么意思 2) 常见原因 3) 修复建议。"
                "语言要平实，面向数学/编程背景的初学者。"
            )
            user = f"Lean 报错：\n{message}"
        else:
            sys = (
                "You are a friendly tutor for the Lean 4 theorem prover. "
                "The user will give you an English error message. "
                "Explain in plain language: 1) what this error means 2) common causes "
                "3) how to fix it. Be concise and beginner-friendly."
            )
            user = f"Lean error:\n{message}"
        if code:
            user += f"\n\nOffending code:\n{code}"
        return self.complete(sys, user)

    def translate_proof(self, lean_proof: str, target_lang: str = "zh") -> str:
        from .proof import translate_source

        results = translate_source(lean_proof, target_lang=target_lang, llm=self)
        if not results:
            return "（未找到证明块）"
        return results[0].pretty()


class OllamaBackend(LLMBackend):
    """本地 Ollama 后端（免费、离线、隐私优先）。"""

    provider = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None, sampling: dict | None = None):
        self._base_url = base_url or os.environ.get(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        self._model = model or os.environ.get("LEANWEAVER_MODEL", "qwen2.5-coder:7b")
        self.sampling = _env_sampling_params()
        if sampling:
            self.sampling.update(sampling)

    def complete(self, system: str, user: str, **kwargs) -> str:
        # Ollama 原生 HTTP API，无需额外依赖
        import json
        import urllib.request

        # 合并采样参数（Ollama 支持 temperature/top_p/stop/seed 等）
        params = dict(self.sampling)
        for k in SUPPORTED_PARAMS:
            if k in kwargs:
                params[k] = kwargs[k]
        params.pop("timeout", None)
        params.pop("max_tokens", None)  # Ollama 用 num_predict
        if "max_tokens" in {**self.sampling, **kwargs}:
            params["num_predict"] = {**self.sampling, **kwargs}["max_tokens"]

        payload = json.dumps(
            {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                **params,
            }
        ).encode()
        req = urllib.request.Request(
            f"{self._base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=kwargs.get("timeout", 120)) as resp:
            data = json.loads(resp.read().decode())
        return data.get("message", {}).get("content", "")

    def explain_error(self, message: str, code: str | None = None, lang: str = "en") -> str:
        if lang == "zh":
            sys = (
                "你是 Lean 4 定理证明器的中文导师。用通俗中文解释下面的 Lean 报错："
                "1) 意思 2) 常见原因 3) 修复建议。"
            )
            user = f"Lean 报错：\n{message}"
        else:
            sys = (
                "You are a friendly tutor for the Lean 4 theorem prover. "
                "Explain the following Lean error in plain English: "
                "1) what it means 2) common causes 3) how to fix it."
            )
            user = f"Lean error:\n{message}"
        if code:
            user += f"\n\nOffending code:\n{code}"
        return self.complete(sys, user)

    def translate_proof(self, lean_proof: str, target_lang: str = "zh") -> str:
        from .proof import translate_source

        results = translate_source(lean_proof, target_lang=target_lang, llm=self)
        if not results:
            return "（未找到证明块）"
        return results[0].pretty()


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
