import subprocess
import json
import base64
import os
from typing import Optional

#timeout for parser execution
PARSER_TIMEOUT = 30
#container name for parser
PARSER_CONTAINER = "parser"

class ParseResult:
    def __init__(self, text: str, metadata: dict, error: Optional[str] = None):
        self.text = text
        self.metadata = metadata
        self.error = error

def parse_document(content: bytes, file_type: str) -> ParseResult:
    #send document to parser container via stdin/stdout IPC
    input_data = json.dumps({
        "content": base64.b64encode(content).decode("utf-8"),
        "file_type": file_type
    })
    #use docker exec in production, direct subprocess for testing
    use_docker = os.environ.get("USE_DOCKER_PARSER", "false").lower() == "true"
    if use_docker:
        cmd = ["docker", "exec", "-i", PARSER_CONTAINER, "python", "-m", "worker"]
    else:
        #direct call for testing without docker
        parser_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "parser")
        cmd = ["python", "-m", "worker"]
        cwd = os.path.abspath(parser_dir)
    try:
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=PARSER_TIMEOUT,
            cwd=cwd if not use_docker else None
        )
        if result.returncode != 0:
            return ParseResult("", {}, error=result.stderr or "Parser failed")
        output = json.loads(result.stdout)
        if "error" in output:
            return ParseResult("", {}, error=output["error"])
        return ParseResult(output.get("text", ""), output.get("metadata", {}))
    except subprocess.TimeoutExpired:
        return ParseResult("", {}, error="Parser timeout")
    except Exception as e:
        return ParseResult("", {}, error=str(e))
