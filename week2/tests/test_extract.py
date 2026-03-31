from unittest.mock import patch

try:
    from ..app.services import extract as extract_module
    from ..app.services.extract import extract_key_challenges_llm, extract_test_factors_llm
except ImportError:
    # 直接运行文件时（非 pytest 包导入），使用绝对导入
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.services import extract as extract_module
    from app.services.extract import extract_key_challenges_llm, extract_test_factors_llm


# --- extract_test_factors_llm 单元测试（mock LLM，无需 Ollama） ---


def test_extract_test_factors_llm_empty_input():
    """空输入返回空列表。"""
    assert extract_test_factors_llm("") == []
    assert extract_test_factors_llm("   \n\t  ") == []


@patch.object(extract_module, "_call_test_factors")
def test_extract_test_factors_llm_bullet_list_input(mock_call):
    """bullet 格式需求：mock 返回若干测试因子。"""
    mock_call.return_value = ["文件格式", "文件大小限制", "用户登录态"]
    result = extract_test_factors_llm("- 上传 jpg/png，大小不超过 2MB\n* 未登录跳转登录页")
    assert result == ["文件格式", "文件大小限制", "用户登录态"]
    mock_call.assert_called_once()


@patch.object(extract_module, "_call_test_factors")
def test_extract_test_factors_llm_keyword_prefixed_input(mock_call):
    """关键词前缀需求：mock 返回测试因子。"""
    mock_call.return_value = ["权限校验", "数据校验"]
    result = extract_test_factors_llm("测试：权限检查。验证：输入格式。")
    assert result == ["权限校验", "数据校验"]
    mock_call.assert_called_once()


@patch.object(extract_module, "_call_test_factors")
def test_extract_test_factors_llm_strips_whitespace(mock_call):
    """输入前后空白会被 trim。"""
    mock_call.return_value = ["因子A"]
    result = extract_test_factors_llm("  \n  需求内容  \n  ")
    assert result == ["因子A"]
    mock_call.assert_called_once_with("需求内容", None)


@patch.object(extract_module, "_call_test_factors")
def test_extract_test_factors_llm_returns_list_of_strings(mock_call):
    """返回值为字符串列表，长度 3–5。"""
    mock_call.return_value = ["A", "B", "C"]
    result = extract_test_factors_llm("some requirements")
    assert isinstance(result, list)
    assert all(isinstance(x, str) for x in result)
    assert len(result) == 3


@patch.object(extract_module, "_call_test_factors")
def test_extract_test_factors_llm_passes_hint(mock_call):
    """用户提示会传给底层调用。"""
    mock_call.return_value = ["X"]
    extract_test_factors_llm("  body  ", "  关注登录态  ")
    mock_call.assert_called_once_with("body", "关注登录态")


# --- extract_key_challenges_llm ---


def test_extract_key_challenges_llm_empty_input():
    assert extract_key_challenges_llm("") == []
    assert extract_key_challenges_llm("   \n  ") == []


@patch.object(extract_module, "_call_key_challenges")
def test_extract_key_challenges_llm_returns_two(mock_call):
    mock_call.return_value = [
        "在弱网下保证上传幂等与断点续传的一致性。",
        "多租户下权限与数据隔离的交叉校验。",
    ]
    result = extract_key_challenges_llm("需求：文件上传与权限……")
    assert result == mock_call.return_value
    assert len(result) == 2
    mock_call.assert_called_once_with("需求：文件上传与权限……", None)


@patch.object(extract_module, "_call_key_challenges")
def test_extract_key_challenges_llm_truncates_to_two(mock_call):
    """模型若返回多于 2 条，由 _call_key_challenges 截断；此处 mock 已截断后的结果。"""
    mock_call.return_value = ["仅一条难点"]
    result = extract_key_challenges_llm("x")
    assert result == ["仅一条难点"]


@patch.object(extract_module, "_call_ollama")
def test_call_key_challenges_truncates_items_to_two(mock_ollama):
    """LLM JSON 中 items 超过 2 条时只保留前 2 条。"""
    mock_ollama.return_value = '{"items": ["一", "二", "三"]}'
    assert extract_module._call_key_challenges("t") == ["一", "二"]
