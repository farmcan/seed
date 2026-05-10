from __future__ import annotations

import base64
import os
from pathlib import Path

from openai import OpenAI


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


def analyze_frames_with_qwen_vl(
    frame_paths: list[Path],
    *,
    model: str = DEFAULT_QWEN_VL_MODEL,
    prompt: str | None = None,
    base_url: str = DEFAULT_DASHSCOPE_BASE_URL,
) -> str:
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
    return str(response.choices[0].message.content or "").strip()


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
