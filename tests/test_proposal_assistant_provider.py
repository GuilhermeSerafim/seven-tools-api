from unittest.mock import patch as mock_patch

import httpx
import pytest

from app.modules.ai.service import call_ai_provider_with_tools


SAMPLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "noop",
            "description": "no-op",
            "parameters": {"type": "object", "properties": {}},
        },
    }
]


@pytest.fixture(autouse=True)
def setup_db():
    yield


def _mock_response(json_body: dict, status: int = 200):
    return httpx.Response(
        status_code=status,
        json=json_body,
        request=httpx.Request("POST", "https://x"),
    )


def test_call_ai_provider_with_tools_returns_message_and_tool_calls():
    payload = {
        "choices": [
            {
                "message": {
                    "content": "ok",
                    "tool_calls": [
                        {
                            "id": "1",
                            "type": "function",
                            "function": {"name": "noop", "arguments": "{}"},
                        }
                    ],
                }
            }
        ]
    }
    with mock_patch("app.modules.ai.service.httpx.post", return_value=_mock_response(payload)) as posted:
        msg = call_ai_provider_with_tools(
            messages=[{"role": "user", "content": "hi"}],
            tools=SAMPLE_TOOLS,
        )
    assert msg["content"] == "ok"
    assert len(msg["tool_calls"]) == 1
    assert msg["tool_calls"][0]["function"]["name"] == "noop"
    sent_body = posted.call_args.kwargs["json"]
    assert "tools" in sent_body
    assert sent_body["tools"] == SAMPLE_TOOLS


def test_call_ai_provider_with_tools_handles_empty_tool_calls():
    payload = {"choices": [{"message": {"content": "só texto"}}]}
    with mock_patch("app.modules.ai.service.httpx.post", return_value=_mock_response(payload)):
        msg = call_ai_provider_with_tools(
            messages=[{"role": "user", "content": "hi"}],
            tools=SAMPLE_TOOLS,
        )
    assert msg["content"] == "só texto"
    assert msg["tool_calls"] == []


def test_call_ai_provider_with_tools_raises_on_5xx():
    with mock_patch("app.modules.ai.service.httpx.post", return_value=_mock_response({}, status=503)):
        with pytest.raises(httpx.HTTPStatusError):
            call_ai_provider_with_tools(
                messages=[{"role": "user", "content": "hi"}],
                tools=SAMPLE_TOOLS,
            )


def test_call_ai_provider_with_tools_omits_response_format():
    payload = {"choices": [{"message": {"content": "ok"}}]}
    with mock_patch("app.modules.ai.service.httpx.post", return_value=_mock_response(payload)) as posted:
        call_ai_provider_with_tools(
            messages=[{"role": "user", "content": "hi"}],
            tools=SAMPLE_TOOLS,
        )
    sent_body = posted.call_args.kwargs["json"]
    assert "response_format" not in sent_body


def test_call_ai_provider_with_tools_uses_configured_generation_settings():
    payload = {"choices": [{"message": {"content": "ok"}}]}
    with (
        mock_patch("app.modules.ai.service.settings.ai_temperature", 0.12),
        mock_patch("app.modules.ai.service.settings.ai_max_tokens", 3456),
        mock_patch("app.modules.ai.service.httpx.post", return_value=_mock_response(payload)) as posted,
    ):
        call_ai_provider_with_tools(
            messages=[{"role": "user", "content": "hi"}],
            tools=SAMPLE_TOOLS,
        )
    sent_body = posted.call_args.kwargs["json"]
    assert sent_body["temperature"] == pytest.approx(0.12)
    assert sent_body["max_tokens"] == 3456
    assert "response_format" not in sent_body
