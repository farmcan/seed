from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from seed.costs import TokenUsage


DEFAULT_QWEN_VL_MODEL = os.getenv("SEED_QWEN_VL_MODEL", "qwen-vl-max")
DEFAULT_DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)
DEFAULT_VISUAL_PROMPT = (
    "请分析这些从同一个视频中按时间抽取的关键帧，输出简洁但具体的视觉笔记。"
    "重点包括：场景变化、屏幕文字、人物/物体/动作、产品或演示证据、剪辑节奏、"
    "视频结构信号、可能的封面/标题信息，以及视觉分析的不确定性。"
)


@dataclass(frozen=True)
class VisionAnalysisResult:
    analysis: str
    usage: TokenUsage


def analyze_frames_with_qwen_vl(
    frame_paths: list[Path],
    *,
    model: str = DEFAULT_QWEN_VL_MODEL,
    prompt: str | None = None,
    base_url: str = DEFAULT_DASHSCOPE_BASE_URL,
) -> str:
    return analyze_frames_with_qwen_vl_result(
        frame_paths,
        model=model,
        prompt=prompt,
        base_url=base_url,
    ).analysis


def analyze_frames_with_qwen_vl_result(
    frame_paths: list[Path],
    *,
    model: str = DEFAULT_QWEN_VL_MODEL,
    prompt: str | None = None,
    base_url: str = DEFAULT_DASHSCOPE_BASE_URL,
) -> VisionAnalysisResult:
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY or QWEN_API_KEY is required for Qwen-VL")
    if not frame_paths:
        raise ValueError("At least one frame is required for visual analysis")

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=build_visual_analysis_messages(frame_paths, prompt=prompt),
        temperature=0,
    )
    return VisionAnalysisResult(
        analysis=str(response.choices[0].message.content or "").strip(),
        usage=token_usage_from_response(response),
    )


def build_visual_analysis_messages(
    frame_paths: list[Path],
    prompt: str | None = None,
) -> list[dict]:
    content = [{"type": "text", "text": prompt or DEFAULT_VISUAL_PROMPT}]
    for path in frame_paths:
        content.append({"type": "image_url", "image_url": {"url": image_data_url(path)}})
    return [{"role": "user", "content": content}]


def image_data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type_for_image(path)};base64,{encoded}"


def mime_type_for_image(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


def token_usage_from_response(response: Any) -> TokenUsage:
    usage = getattr(response, "usage", None)
    return TokenUsage.from_counts(
        input_tokens=usage_value(usage, "prompt_tokens", "input_tokens"),
        output_tokens=usage_value(usage, "completion_tokens", "output_tokens"),
        total_tokens=usage_value(usage, "total_tokens"),
    )


def usage_value(usage: Any, *names: str) -> int | None:
    if usage is None:
        return None
    for name in names:
        if isinstance(usage, dict) and usage.get(name) is not None:
            return int(usage[name])
        value = getattr(usage, name, None)
        if value is not None:
            return int(value)
    return None
