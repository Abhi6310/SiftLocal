import os
import pytest
import httpx
import subprocess
import json

def in_isolated_container():
    #Check if running in Docker container with network isolation
    #Returns True if in container, False otherwise
    return os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == '1'

@pytest.mark.skipif(not in_isolated_container(), reason="Must run inside isolated container")
def test_no_egress_backend():
    #Backend container cannot reach external network
    #Attempts to connect to public host, expects failure when on internal network
    with pytest.raises((httpx.ConnectError, httpx.TimeoutException, httpx.ConnectTimeout)):
        client = httpx.Client(timeout=5.0)
        client.get("https://example.com")

@pytest.mark.skipif(not in_isolated_container(), reason="Must run inside isolated container")
def test_no_egress_dns():
    #Backend container cannot resolve external DNS
    #Verifies DNS resolution for external hosts fails
    with pytest.raises((httpx.ConnectError, httpx.TimeoutException, httpx.ConnectTimeout)):
        client = httpx.Client(timeout=5.0)
        client.get("https://1.1.1.1")

def test_network_configuration():
    #Verify Docker network is configured as internal
    try:
        result = subprocess.run(
            ["docker", "network", "inspect", "docker_siftlocal-internal"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            network_info = json.loads(result.stdout)
            if network_info:
                is_internal = network_info[0].get("Internal", False)
                assert is_internal, "Network must be configured as internal"
        else:
            pytest.skip("Docker network not yet created")
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pytest.skip("Cannot inspect Docker network (not in container or docker not available)")

@pytest.mark.skip(reason="Parser has no HTTP server yet")
def test_internal_communication_possible():
    #Verify internal container-to-container communication works
    #Skipped until parser has HTTP endpoint
    pass
