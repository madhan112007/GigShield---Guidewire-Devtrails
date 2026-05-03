"""
SUSANOO BEDROCK CLIENT
Wraps boto3 Bedrock Runtime with retry, fallback model, and response parsing.
Supports: meta.llama3 and anthropic.claude formats.
"""
import json
import asyncio
import logging
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from app.config import settings

logger = logging.getLogger(__name__)

_PRIMARY_MODEL   = getattr(settings, "BEDROCK_MODEL_ID", "meta.llama3-8b-instruct-v1:0")
_FALLBACK_MODEL  = getattr(settings, "BEDROCK_MODEL_FALLBACK", "mistral.mistral-7b-instruct-v0:2")
_REGION          = getattr(settings, "AWS_REGION", "ap-south-1")
_MAX_TOKENS      = getattr(settings, "CHAT_MAX_TOKENS", 400)


def _make_client():
    return boto3.client(
        "bedrock-runtime",
        region_name=_REGION,
        config=Config(retries={"max_attempts": 3, "mode": "adaptive"}),
    )


def _build_body(model_id: str, messages: list, system: str, max_tokens: int) -> dict:
    """Build request body based on model family."""
    if "llama" in model_id:
        # Llama 3 uses a single prompt string
        prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system}<|eot_id|>"
        for m in messages:
            role = m["role"]
            content = m["content"]
            prompt += f"<|start_header_id|>{role}<|end_header_id|>\n{content}<|eot_id|>"
        prompt += "<|start_header_id|>assistant<|end_header_id|>\n"
        return {
            "prompt": prompt,
            "max_gen_len": max_tokens,
            "temperature": 0.2,
            "top_p": 0.9,
        }
    elif "mistral" in model_id:
        prompt = f"<s>[INST] {system}\n\n"
        for m in messages:
            if m["role"] == "user":
                prompt += m["content"] + " [/INST] "
            else:
                prompt += m["content"] + " </s><s>[INST] "
        return {"prompt": prompt, "max_tokens": max_tokens, "temperature": 0.2}
    else:
        # Claude / Anthropic format
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
            "temperature": 0.2,
        }


def _extract_text(model_id: str, response_body: dict) -> str:
    """Extract text from response based on model family."""
    if "llama" in model_id:
        return response_body.get("generation", "")
    elif "mistral" in model_id:
        outputs = response_body.get("outputs", [{}])
        return outputs[0].get("text", "") if outputs else ""
    else:
        content = response_body.get("content", [{}])
        return content[0].get("text", "") if content else ""


async def invoke(messages: list, system: str, max_tokens: int = _MAX_TOKENS) -> str:
    """
    Invoke Bedrock with primary model, fall back to secondary on throttle/error.
    Returns raw text from the model.
    """
    client = _make_client()
    loop = asyncio.get_event_loop()

    for model_id in [_PRIMARY_MODEL, _FALLBACK_MODEL]:
        try:
            body = _build_body(model_id, messages, system, max_tokens)
            response = await loop.run_in_executor(
                None,
                lambda: client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json",
                ),
            )
            result = json.loads(response["body"].read())
            text = _extract_text(model_id, result).strip()
            logger.info(f"[Bedrock] model={model_id} tokens~={len(text)//4}")
            return text
        except ClientError as e:
            code = e.response["Error"]["Code"]
            logger.warning(f"[Bedrock] {model_id} error={code}, trying fallback")
            if model_id == _FALLBACK_MODEL:
                raise
        except Exception as e:
            logger.error(f"[Bedrock] {model_id} unexpected error: {e}")
            if model_id == _FALLBACK_MODEL:
                raise
    return ""
