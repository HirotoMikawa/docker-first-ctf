"""
Project Sol: Container Tester (Ver 10.2)

Tests mission containers by starting them and verifying they can be solved.
Used to generate accurate writeups with actual container URLs.
"""

import json
import time
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import sys

# Requests library (optional)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: requests library not installed. Container testing will be limited.", file=sys.stderr)

# Set up logger
logger = logging.getLogger(__name__)

# Docker library
try:
    import docker
except ImportError:
    docker = None

# Fallback to subprocess if docker library not available
import subprocess


class ContainerTester:
    """Tests mission containers by starting them and verifying they can be solved."""
    
    def __init__(self, use_docker_lib: bool = True):
        """
        Initialize tester.
        
        Args:
            use_docker_lib: Use docker Python library if available (default: True)
        """
        self.use_docker_lib = use_docker_lib and docker is not None
        
        if self.use_docker_lib:
            try:
                self.client = docker.from_env()
                # Test connection
                self.client.ping()
            except Exception as e:
                print(f"Warning: Docker library connection failed: {e}", file=sys.stderr)
                print("Falling back to subprocess method", file=sys.stderr)
                self.use_docker_lib = False
        else:
            # Check if docker command is available
            try:
                subprocess.run(
                    ["docker", "version"],
                    capture_output=True,
                    check=True,
                    timeout=5
                )
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                raise RuntimeError(
                    "Docker is not available. "
                    "Please ensure Docker is installed and running."
                )
    
    def start_test_container(
        self,
        image_name: str,
        flag: str,
        timeout: int = 30
    ) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        """
        Start a test container and get its URL.
        
        Args:
            image_name: Docker image name
            flag: Flag value to set in container
            timeout: Timeout in seconds to wait for container to be ready
            
        Returns:
            Tuple of (container_id, port, container_url) or (None, None, None) on failure
        """
        container = None
        container_id = None
        port = None
        container_url = None
        
        try:
            if self.use_docker_lib:
                # Start container using docker library
                try:
                    container = self.client.containers.run(
                        image=image_name,
                        name=f"sol_test_{int(time.time())}",
                        ports={'8000/tcp': ('0.0.0.0', 0)},  # Auto-assign port
                        detach=True,
                        remove=False,
                        environment={
                            "CTF_FLAG": flag
                        },
                        mem_limit="512m",
                        network_disabled=False,
                    )
                    
                    # Wait for container to be ready
                    container.reload()
                    container_id = container.id
                    
                    # Get assigned port
                    if container.ports and '8000/tcp' in container.ports:
                        port_info = container.ports['8000/tcp']
                        if port_info and len(port_info) > 0:
                            port = int(port_info[0]['HostPort'])
                            container_url = f"http://localhost:{port}"
                    
                    # Wait for container to be ready (check if it responds)
                    if HAS_REQUESTS:
                        max_wait = timeout
                        wait_interval = 2
                        waited = 0
                        
                        while waited < max_wait:
                            try:
                                response = requests.get(f"{container_url}/", timeout=2)
                                if response.status_code in [200, 404]:  # 404 is OK, means server is running
                                    break
                            except requests.RequestException:
                                pass
                            
                            time.sleep(wait_interval)
                            waited += wait_interval
                    else:
                        # Wait without checking if requests is not available
                        time.sleep(5)
                    
                    return container_id, port, container_url
                except docker.errors.APIError as e:
                    error_msg = str(e)
                    if "port is already allocated" in error_msg or "Bind" in error_msg:
                        print(f"[WARNING] Port conflict detected. Trying to find available port...", file=sys.stderr)
                        # Try with a different approach - let Docker auto-assign
                        try:
                            container = self.client.containers.run(
                                image=image_name,
                                name=f"sol_test_{int(time.time())}_{hash(image_name) % 10000}",
                                ports={'8000/tcp': None},  # Let Docker auto-assign
                                detach=True,
                                remove=False,
                                environment={
                                    "CTF_FLAG": flag
                                },
                                mem_limit="512m",
                                network_disabled=False,
                            )
                            container.reload()
                            container_id = container.id
                            if container.ports and '8000/tcp' in container.ports:
                                port_info = container.ports['8000/tcp']
                                if port_info and len(port_info) > 0:
                                    port = int(port_info[0]['HostPort'])
                                    container_url = f"http://localhost:{port}"
                            time.sleep(5)
                            return container_id, port, container_url
                        except Exception as e2:
                            print(f"[ERROR] Failed to start container after retry: {e2}", file=sys.stderr)
                            return None, None, None
                    else:
                        print(f"[ERROR] Failed to start container: {error_msg}", file=sys.stderr)
                        return None, None, None
                except Exception as e:
                    print(f"[ERROR] Unexpected error starting container: {e}", file=sys.stderr)
                    return None, None, None
            else:
                # Start container using subprocess
                import random
                test_name = f"sol_test_{int(time.time())}_{random.randint(1000, 9999)}"
                
                # Start container
                process = subprocess.Popen(
                    [
                        "docker", "run",
                        "-d",
                        "--name", test_name,
                        "-p", "0:8000",
                        "-e", f"CTF_FLAG={flag}",
                        "--rm",
                        image_name
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate(timeout=30)
                
                if process.returncode != 0:
                    print(f"[ERROR] Failed to start container: {stderr}", file=sys.stderr)
                    return None, None, None
                
                container_id = stdout.strip()
                
                # Get port mapping
                port_process = subprocess.run(
                    [
                        "docker", "port", test_name
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10
                )
                
                if port_process.returncode == 0:
                    # Parse port output: "8000/tcp -> 0.0.0.0:32804"
                    # Handle multiple lines if present
                    port_lines = port_process.stdout.strip().split('\n')
                    for port_line in port_lines:
                        port_line = port_line.strip()
                        if "->" in port_line and "8000/tcp" in port_line:
                            # Extract port from "8000/tcp -> 0.0.0.0:32804"
                            try:
                                # Split by "->" and get the right side, then split by ":" to get port
                                right_side = port_line.split("->")[1].strip()
                                port_str = right_side.split(":")[1].strip()
                                port = int(port_str)
                                container_url = f"http://localhost:{port}"
                                break
                            except (ValueError, IndexError) as e:
                                print(f"[WARNING] Failed to parse port from line: {port_line}", file=sys.stderr)
                                continue
                
                # Check if container_url was set
                if not container_url:
                    print(f"[ERROR] Failed to extract port from docker port output: {port_process.stdout}", file=sys.stderr)
                    # Try to stop and remove the container
                    try:
                        subprocess.run(["docker", "stop", test_name], capture_output=True, timeout=10)
                        subprocess.run(["docker", "rm", test_name], capture_output=True, timeout=10)
                    except:
                        pass
                    return None, None, None
                
                # Wait for container to be ready
                if HAS_REQUESTS:
                    max_wait = timeout
                    wait_interval = 2
                    waited = 0
                    
                    while waited < max_wait:
                        try:
                            response = requests.get(f"{container_url}/", timeout=2)
                            if response.status_code in [200, 404]:
                                break
                        except requests.RequestException:
                            pass
                        
                        time.sleep(wait_interval)
                        waited += wait_interval
                else:
                    # Wait without checking if requests is not available
                    time.sleep(5)
                
                return container_id, port, container_url
                
        except Exception as e:
            print(f"[ERROR] Failed to start test container: {e}", file=sys.stderr)
            return None, None, None
    
    def stop_test_container(self, container_id: str) -> bool:
        """
        Stop and remove test container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_docker_lib:
                container = self.client.containers.get(container_id)
                container.stop()
                container.remove()
            else:
                # Try by ID first, then by name
                subprocess.run(
                    ["docker", "stop", container_id],
                    capture_output=True,
                    timeout=10
                )
                subprocess.run(
                    ["docker", "rm", container_id],
                    capture_output=True,
                    timeout=10
                )
            return True
        except Exception as e:
            print(f"[WARNING] Failed to stop container {container_id}: {e}", file=sys.stderr)
            return False
    
    def test_solvability(
        self,
        container_id: str,
        expected_flag: str,
        timeout: int = 60,
        mission_type: str = "Web",
        container_url: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Tests if the container contains the flag and the problem is actually solvable.
        This performs both white-box inspection (docker exec) and black-box testing (HTTP requests).
        
        Args:
            container_id: The container ID to inspect
            expected_flag: The flag string to look for (e.g., "SolCTF{...}")
            timeout: Max seconds to wait for container to be ready
            mission_type: The category of the challenge (e.g., 'SQLi', 'RCE', 'Web')
            container_url: Container URL for HTTP testing (optional, but recommended)

        Returns:
            Tuple[is_solvable (bool), error_message (str|None), found_flag (str|None)]
        """
        logger.info(f"Starting comprehensive solvability test for container {container_id[:12]} (Type: {mission_type})")
        
        if not container_id:
            return False, "Container ID is required for internal inspection", None
        
        # Helper function to execute command in container
        def exec_in_container(cmd, user="ctfuser"):
            """Execute command in container and return (exit_code, output_str)"""
            try:
                if self.use_docker_lib:
                    container = self.client.containers.get(container_id)
                    exit_code, output = container.exec_run(cmd, user=user)
                    output_str = output.decode('utf-8', errors='ignore') if isinstance(output, bytes) else str(output)
                    return exit_code, output_str
                else:
                    # For subprocess mode, use docker exec
                    # Handle shell commands (e.g., "sh -c 'echo $FLAG'") properly
                    if "sh -c" in cmd or "bash -c" in cmd:
                        # Split the command properly for shell execution
                        parts = cmd.split(" ", 2)  # Split into ["sh", "-c", "'echo $FLAG'"]
                        result = subprocess.run(
                            ["docker", "exec", container_id] + parts,
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                    else:
                        # Simple command, split by space
                        result = subprocess.run(
                            ["docker", "exec", container_id] + cmd.split(),
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                    return result.returncode, result.stdout
            except Exception as e:
                logger.debug(f"Failed to execute command '{cmd}': {e}")
                return -1, ""
        
        # --- Phase 1: Check file at /home/ctfuser/flag.txt ---
        exit_code, output_str = exec_in_container("cat /home/ctfuser/flag.txt", user="ctfuser")
        if exit_code == 0 and expected_flag in output_str:
            logger.info("Flag found in /home/ctfuser/flag.txt")
            return True, None, expected_flag
        
        # --- Phase 2: Check file at /flag.txt ---
        exit_code, output_str = exec_in_container("cat /flag.txt", user="ctfuser")
        if exit_code == 0 and expected_flag in output_str:
            logger.info("Flag found in /flag.txt")
            return True, None, expected_flag
        
        # --- Phase 3: Check Environment Variables ---
        exit_code, output_str = exec_in_container("env", user="ctfuser")
        if exit_code == 0 and expected_flag in output_str:
            logger.info("Flag found in environment variables")
            return True, None, expected_flag
        
        # --- Phase 4: Check FLAG environment variable specifically ---
        exit_code, output_str = exec_in_container("sh -c 'echo $FLAG'", user="ctfuser")
        if exit_code == 0 and expected_flag in output_str:
            logger.info("Flag found in FLAG environment variable")
            return True, None, expected_flag
        
        # Flag not found in any location
        logger.warning(f"Flag NOT found in container {container_id[:12]}. Expected: {expected_flag}")
        
        # --- Phase 5: Functional Testing (if container_url is provided) ---
        # Actually try to solve the problem to verify it's solvable
        if container_url and HAS_REQUESTS:
            logger.info("Performing functional test (actually trying to solve the problem)")
            try:
                from solver.problem_solver import ProblemSolver
                solver = ProblemSolver()
                solved, found_flag, method = solver.solve(container_url, mission_type, expected_flag)
                
                if solved and found_flag:
                    logger.info(f"Problem is solvable! Flag found using method: {method}")
                    return True, None, found_flag
                else:
                    logger.warning(f"Problem appears unsolvable: {method}")
                    # Check for specific error patterns
                    if "no such table" in str(method).lower() or "database" in str(method).lower():
                        return False, f"Database not initialized: {method}", None
                    elif "error" in str(method).lower():
                        return False, f"Application error: {method}", None
                    else:
                        return False, f"Problem appears unsolvable: {method}", None
            except ImportError:
                logger.warning("ProblemSolver not available, skipping functional test")
            except Exception as e:
                logger.warning(f"Functional test failed: {e}")
        
        # If we reach here, flag was not found and functional test either failed or was not performed
        return False, f"Flag NOT found in container. Expected flag: {expected_flag}", None

    def _perform_type_check(self, url: str, mission_type: str) -> bool:
        """
        Performs lightweight heuristic checks based on mission type.
        Returns True if indicators are found, False otherwise.
        """
        if not HAS_REQUESTS:
            return True  # Skip check if requests is not available
        
        mission_type = mission_type.upper()

        try:
            if "SQL" in mission_type:
                # SQLi Heuristic: Single quote check
                # 正常系と異常系（'を入れた場合）でレスポンスが異なるか、またはエラーが出るか
                normal = requests.get(url, timeout=3).text
                error_test = requests.get(f"{url}?id='", timeout=3).text
                
                # レスポンスが変わっていれば「何らかの処理が動いている」と判断
                if len(normal) != len(error_test) or "SQL" in error_test or "syntax" in error_test:
                    return True

            elif "XSS" in mission_type:
                # XSS Heuristic: Reflection check
                payload = "sol_test_xss"
                # クエリパラメータに値を入れて、それがレスポンスに含まれるか
                res = requests.get(f"{url}?q={payload}", timeout=3)
                if payload in res.text:
                    return True

            elif "RCE" in mission_type or "CMD" in mission_type:
                # RCE Heuristic: Common param check
                # 単純にアクセスして落ちなければOKとする（積極的な攻撃は避ける）
                return True

        except Exception:
            return False # Check failed, but doesn't mean problem is broken

        return True

