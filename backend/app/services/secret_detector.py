import re
import math
from pydantic import BaseModel
from typing import List, Tuple, Pattern

class SecretPattern(BaseModel):
    name: str
    pattern: str
    confidence: float

class SecretEntity(BaseModel):
    secret_type: str
    start: int
    end: int
    confidence: float
    text: str

#compiled patterns for performance
_COMPILED_PATTERNS: List[Tuple[SecretPattern, Pattern]] = []

SECRET_PATTERNS: List[SecretPattern] = [
    #API keys - definitive formats (1.0)
    SecretPattern(name="AWS_ACCESS_KEY", pattern=r"AKIA[0-9A-Z]{16}", confidence=1.0),
    SecretPattern(name="GITHUB_TOKEN_CLASSIC", pattern=r"ghp_[a-zA-Z0-9]{36}", confidence=1.0),
    SecretPattern(name="GITHUB_TOKEN_FINE_GRAINED", pattern=r"github_pat_[a-zA-Z0-9_]{82}", confidence=1.0),
    #private key headers (0.9)
    SecretPattern(name="PRIVATE_KEY_RSA", pattern=r"-----BEGIN RSA PRIVATE KEY-----", confidence=0.9),
    SecretPattern(name="PRIVATE_KEY_OPENSSH", pattern=r"-----BEGIN OPENSSH PRIVATE KEY-----", confidence=0.9),
    SecretPattern(name="PRIVATE_KEY_PGP", pattern=r"-----BEGIN PGP PRIVATE KEY BLOCK-----", confidence=0.9),
    SecretPattern(name="PRIVATE_KEY_GENERIC", pattern=r"-----BEGIN [A-Z ]+ PRIVATE KEY-----", confidence=0.9),
    #service tokens (0.9)
    SecretPattern(name="SLACK_TOKEN", pattern=r"xox[baprs]-[0-9a-zA-Z\-]{10,}", confidence=0.9),
    SecretPattern(name="STRIPE_SECRET_KEY", pattern=r"sk_live_[0-9a-zA-Z]{24,}", confidence=0.9),
    SecretPattern(name="STRIPE_TEST_KEY", pattern=r"sk_test_[0-9a-zA-Z]{24,}", confidence=0.9),
    SecretPattern(name="GOOGLE_API_KEY", pattern=r"AIza[0-9A-Za-z\-_]{35}", confidence=0.9),
    #bearer/jwt (0.8)
    SecretPattern(name="BEARER_TOKEN", pattern=r"Bearer\s+[a-zA-Z0-9\-._~+/]+=*", confidence=0.8),
    SecretPattern(name="JWT", pattern=r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+", confidence=0.8),
    #db connection strings (0.8)
    SecretPattern(name="DB_CONNECTION_STRING", pattern=r"(?:postgres|mysql|redis|mongodb)://[a-zA-Z0-9_]+:[^@\s]+@[a-zA-Z0-9_.\-]+", confidence=0.8),
    #internal IPs (0.7)
    SecretPattern(name="INTERNAL_IP", pattern=r"(?:^|\D)((?:10\.\d{1,3}\.\d{1,3}\.\d{1,3})|(?:172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})|(?:192\.168\.\d{1,3}\.\d{1,3}))(?=\D|$)", confidence=0.7),
    #generic patterns (0.7)
    SecretPattern(name="GENERIC_API_KEY", pattern=r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9\-_]{16,})['\"]?", confidence=0.7),
    SecretPattern(name="PASSWORD_ASSIGNMENT", pattern=r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"]{8,})['\"]?", confidence=0.7),
]

#entropy config for high-entropy string detection
ENTROPY_THRESHOLD = 4.5
MIN_TOKEN_LENGTH = 16
ENTROPY_CONFIDENCE = 0.6

def _get_compiled_patterns() -> List[Tuple[SecretPattern, Pattern]]:
    global _COMPILED_PATTERNS
    if not _COMPILED_PATTERNS:
        _COMPILED_PATTERNS = [(sp, re.compile(sp.pattern)) for sp in SECRET_PATTERNS]
    return _COMPILED_PATTERNS

def _shannon_entropy(data: str) -> float:
    if not data:
        return 0
    entropy = 0
    for x in set(data):
        p_x = data.count(x) / len(data)
        entropy += -p_x * math.log2(p_x)
    return entropy

def _is_overlapping(start: int, end: int, ranges: List[Tuple[int, int]]) -> bool:
    for r_start, r_end in ranges:
        if max(start, r_start) < min(end, r_end):
            return True
    return False

def detect_secrets(text: str, min_confidence: float = 0.7) -> List[SecretEntity]:
    results = []
    compiled = _get_compiled_patterns()
    for sp, pattern in compiled:
        if sp.confidence < min_confidence:
            continue
        for match in pattern.finditer(text):
            #handle patterns with capture groups (generic api key, password)
            if match.lastindex and match.lastindex > 0:
                #use the last capture group for the actual secret value
                span = match.span(match.lastindex)
                matched_text = match.group(match.lastindex)
            else:
                span = match.span()
                matched_text = match.group()
            results.append(SecretEntity(
                secret_type=sp.name,
                start=span[0],
                end=span[1],
                confidence=sp.confidence,
                text=matched_text
            ))
    #entropy detection for high-entropy strings
    if ENTROPY_CONFIDENCE >= min_confidence:
        covered_ranges = sorted([(r.start, r.end) for r in results])
        for match in re.finditer(r'\S+', text):
            word = match.group()
            start, end = match.span()
            if len(word) < MIN_TOKEN_LENGTH:
                continue
            if _is_overlapping(start, end, covered_ranges):
                continue
            entropy = _shannon_entropy(word)
            if entropy > ENTROPY_THRESHOLD:
                results.append(SecretEntity(
                    secret_type="HIGH_ENTROPY_STRING",
                    start=start,
                    end=end,
                    confidence=min(entropy / 6.0, 1.0),
                    text=word
                ))
    #sort by start position
    results.sort(key=lambda x: x.start)
    return results

def get_patterns() -> List[SecretPattern]:
    return SECRET_PATTERNS
