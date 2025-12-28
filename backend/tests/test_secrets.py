import pytest
from app.services.secret_detector import detect_secrets, get_patterns, SecretPattern

def test_detect_aws_key():
    text = "My AWS key is AKIAIOSFODNN7EXAMPLE and it works."
    results = detect_secrets(text)
    assert len(results) == 1
    assert results[0].secret_type == "AWS_ACCESS_KEY"
    assert results[0].text == "AKIAIOSFODNN7EXAMPLE"
    assert results[0].confidence == 1.0

def test_detect_github_token():
    text = "Use this token: ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789"
    results = detect_secrets(text)
    assert len(results) == 1
    assert results[0].secret_type == "GITHUB_TOKEN_CLASSIC"
    assert results[0].text == "ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789"

def test_detect_private_key():
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBA..."
    results = detect_secrets(text)
    assert len(results) >= 1
    key_result = next((r for r in results if r.secret_type == "PRIVATE_KEY_RSA"), None)
    assert key_result is not None
    assert key_result.confidence == 0.9

def test_detect_generic_api_key():
    text = "config.api_key = 'abcd1234efgh5678ijkl'"
    results = detect_secrets(text)
    match = next((r for r in results if r.secret_type == "GENERIC_API_KEY"), None)
    assert match is not None
    assert match.text == "abcd1234efgh5678ijkl"
    #should not capture the "api_key =" part
    assert "api_key" not in match.text

def test_detect_password():
    text = "password = 'SuperSecret123!'"
    results = detect_secrets(text)
    match = next((r for r in results if r.secret_type == "PASSWORD_ASSIGNMENT"), None)
    assert match is not None
    assert match.text == "SuperSecret123!"
    assert "password" not in match.text

def test_detect_multiple_secrets():
    text = """
    AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
    GITHUB_TOKEN=ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789
    password = "mypassword123"
    """
    results = detect_secrets(text)
    types = {r.secret_type for r in results}
    assert "AWS_ACCESS_KEY" in types
    assert "GITHUB_TOKEN_CLASSIC" in types
    assert "PASSWORD_ASSIGNMENT" in types

def test_no_false_positives():
    text = "This is normal text without any secrets. Just a regular document about API design."
    results = detect_secrets(text)
    #filter out high entropy results - we're testing regex false positives
    regex_results = [r for r in results if r.secret_type != "HIGH_ENTROPY_STRING"]
    assert len(regex_results) == 0

def test_confidence_filtering():
    text = """
    AKIAIOSFODNN7EXAMPLE
    password = "mysecret123"
    """
    #min_confidence=0.9 should only return AWS key
    high_conf = detect_secrets(text, min_confidence=0.9)
    assert len(high_conf) == 1
    assert high_conf[0].secret_type == "AWS_ACCESS_KEY"
    #min_confidence=0.7 should return both
    low_conf = detect_secrets(text, min_confidence=0.7)
    assert len(low_conf) >= 2

def test_get_patterns():
    patterns = get_patterns()
    assert len(patterns) > 0
    assert all(isinstance(p, SecretPattern) for p in patterns)
    assert all(hasattr(p, 'name') and hasattr(p, 'pattern') and hasattr(p, 'confidence') for p in patterns)

def test_high_entropy_detection():
    #random string with high entropy (mix of cases, numbers, symbols)
    random_token = "aB3$xZ9!qW7@mN5#pL2^vK8&cF4*"
    text = f"Here is the token: {random_token}"
    results = detect_secrets(text, min_confidence=0.5)
    match = next((r for r in results if r.secret_type == "HIGH_ENTROPY_STRING"), None)
    assert match is not None
    assert match.text == random_token

def test_ignore_low_entropy():
    #long English words should not be flagged despite length
    text = "This is an internationalization and telecommunications example."
    results = detect_secrets(text, min_confidence=0.5)
    entropy_results = [r for r in results if r.secret_type == "HIGH_ENTROPY_STRING"]
    assert len(entropy_results) == 0

def test_overlap_priority():
    #AWS keys are high entropy but should only be classified as AWS_ACCESS_KEY
    text = "AKIAIOSFODNN7EXAMPLE"
    results = detect_secrets(text, min_confidence=0.5)
    assert len(results) == 1
    assert results[0].secret_type == "AWS_ACCESS_KEY"

def test_internal_ip():
    text = "Connect to 192.168.1.55 for the database."
    results = detect_secrets(text)
    match = next((r for r in results if r.secret_type == "INTERNAL_IP"), None)
    assert match is not None
    assert "192.168.1.55" in match.text
