"""
Project Sol: Image Builder (Ver 10.2)

Builds Docker images for mission containers.
Implements Phase 3.75: Image Build.

Uses docker Python library or subprocess.
"""

import json
import os
import tempfile
import shutil
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Docker library
try:
    import docker
except ImportError:
    docker = None

# Fallback to subprocess if docker library not available
import subprocess


class ImageBuilder:
    """Builds Docker images for mission containers."""
    
    def __init__(self, use_docker_lib: bool = True):
        """
        Initialize builder.
        
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
    
    def _create_dockerfile(self, base_image: str = "python:3.11-slim") -> str:
        """
        Create a temporary Dockerfile for the mission container.
        
        Args:
            base_image: Base image to use (default: python:3.11-slim)
            
        Returns:
            Dockerfile content as string
        """
        # Check if base image is Alpine-based
        is_alpine = "alpine" in base_image.lower()
        
        if is_alpine:
            # Case A: Alpine-based image
            # Alpine uses 'adduser' instead of 'useradd'
            # Python3 needs to be installed
            dockerfile_content = f"""FROM {base_image}

# Python3のインストールとユーザー作成 (Alpine流)
# PROJECT_MASTER.md: User: ctfuser (UID >= 1000) ONLY. Root prohibited.
RUN apk add --no-cache python3 && \\
    adduser -D -u 1000 ctfuser && \\
    echo '<html><body style="background-color:black; color:lime; display:flex; justify-content:center; align-items:center; height:100vh; font-family:monospace;"><h1>Mission Started: Target System Online</h1></body></html>' > /home/ctfuser/index.html

USER ctfuser

WORKDIR /home/ctfuser

# ポート8000でWebサーバーを起動するだけ（仮のコンテナ）
# PROJECT_MASTER.md: Expose: 8000/tcp ONLY.
EXPOSE 8000

# 環境変数CTF_FLAGを注入可能にする（デフォルト値）
ENV CTF_FLAG=SolCTF{{default_flag}}

CMD ["python3", "-m", "http.server", "8000"]
"""
        else:
            # Case B: Debian/Python-Slim-based image
            # Python is already included, use 'useradd'
            dockerfile_content = f"""FROM {base_image}

# ユーザー作成 (Debian流)
# PROJECT_MASTER.md: User: ctfuser (UID >= 1000) ONLY. Root prohibited.
RUN useradd -m -u 1000 ctfuser && \\
    echo '<html><body style="background-color:black; color:lime; display:flex; justify-content:center; align-items:center; height:100vh; font-family:monospace;"><h1>Mission Started: Target System Online</h1></body></html>' > /home/ctfuser/index.html

USER ctfuser

WORKDIR /home/ctfuser

# ポート8000でWebサーバーを起動するだけ（仮のコンテナ）
# PROJECT_MASTER.md: Expose: 8000/tcp ONLY.
EXPOSE 8000

# 環境変数CTF_FLAGを注入可能にする（デフォルト値）
ENV CTF_FLAG=SolCTF{{default_flag}}

CMD ["python3", "-m", "http.server", "8000"]
"""
        
        return dockerfile_content
    
    def _build_with_docker_lib(self, image_name: str, dockerfile_path: str, build_context: str) -> bool:
        """
        Build Docker image using docker Python library.
        
        Args:
            image_name: Name of the image to build
            dockerfile_path: Path to Dockerfile
            build_context: Build context directory
            
        Returns:
            True if build successful, False otherwise
        """
        try:
            print(f"[BUILD] Building image: {image_name}")
            print(f"[BUILD] Using Dockerfile: {dockerfile_path}")
            print(f"[BUILD] Build context: {build_context}")
            
            # Build the image
            image, build_logs = self.client.images.build(
                path=build_context,
                dockerfile=dockerfile_path,
                tag=image_name,
                rm=True,  # Remove intermediate containers
                forcerm=True  # Force remove intermediate containers
            )
            
            # Print build logs
            for log in build_logs:
                if 'stream' in log:
                    print(log['stream'], end='')
                elif 'error' in log:
                    print(f"[ERROR] {log['error']}", file=sys.stderr)
                    return False
            
            print(f"[SUCCESS] Image built successfully: {image_name}")
            print(f"[INFO] Image ID: {image.id}")
            return True
            
        except docker.errors.BuildError as e:
            print(f"[ERROR] Build failed: {e}", file=sys.stderr)
            for log in e.build_log:
                if 'stream' in log:
                    print(log['stream'], end='', file=sys.stderr)
                elif 'error' in log:
                    print(f"[ERROR] {log['error']}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"[ERROR] Unexpected error during build: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False
    
    def _build_with_subprocess(self, image_name: str, dockerfile_path: str, build_context: str) -> bool:
        """
        Build Docker image using subprocess (docker command).
        
        Args:
            image_name: Name of the image to build
            dockerfile_path: Path to Dockerfile
            build_context: Build context directory
            
        Returns:
            True if build successful, False otherwise
        """
        try:
            print(f"[BUILD] Building image: {image_name}")
            print(f"[BUILD] Using Dockerfile: {dockerfile_path}")
            print(f"[BUILD] Build context: {build_context}")
            
            # Run docker build command
            process = subprocess.Popen(
                [
                    "docker", "build",
                    "-f", dockerfile_path,
                    "-t", image_name,
                    build_context
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output in real-time
            for line in process.stdout:
                print(line, end='')
            
            process.wait()
            
            if process.returncode == 0:
                print(f"[SUCCESS] Image built successfully: {image_name}")
                return True
            else:
                print(f"[ERROR] Build failed with exit code {process.returncode}", file=sys.stderr)
                return False
                
        except FileNotFoundError:
            raise RuntimeError(
                "Docker command not found. "
                "Please ensure Docker is installed and available in PATH."
            )
        except Exception as e:
            print(f"[ERROR] Unexpected error during build: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False
    
    def build(self, file_path: str) -> bool:
        """
        Build Docker image from mission JSON file.
        
        Args:
            file_path: Path to mission JSON file
            
        Returns:
            True if build successful, False otherwise
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid or missing required fields
            RuntimeError: If Docker is not available
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read and parse JSON
        try:
            with open(path, 'r', encoding='utf-8') as f:
                mission_json = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading file {file_path}: {e}")
        
        # Extract image name and base image
        environment = mission_json.get("environment", {})
        image_name = environment.get("image")
        base_image = environment.get("base_image", "python:3.11-slim")
        
        if not image_name:
            raise ValueError(
                f"Missing 'environment.image' field in JSON file {file_path}. "
                "Please ensure the JSON contains a valid image name."
            )
        
        # Extract files object from JSON
        files = mission_json.get("files", {})
        
        # Create temporary directory for build context
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="sol_build_")
            
            # Write files from JSON to temporary directory
            if files:
                # Use files from JSON (AI-generated code)
                print(f"[INFO] Using AI-generated files from JSON")
                for filename, content in files.items():
                    file_path = os.path.join(temp_dir, filename)
                    # Create directory if needed
                    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else temp_dir, exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"[INFO] Created file: {filename}")
            else:
                # Fallback: Generate minimal Dockerfile if files not present
                print(f"[WARNING] No 'files' object in JSON, using fallback Dockerfile", file=sys.stderr)
                dockerfile_path = os.path.join(temp_dir, "Dockerfile")
                dockerfile_content = self._create_dockerfile(base_image)
                with open(dockerfile_path, 'w', encoding='utf-8') as f:
                    f.write(dockerfile_content)
            
            # Ensure Dockerfile exists
            dockerfile_path = os.path.join(temp_dir, "Dockerfile")
            if not os.path.exists(dockerfile_path):
                # Generate fallback Dockerfile
                dockerfile_content = self._create_dockerfile(base_image)
                with open(dockerfile_path, 'w', encoding='utf-8') as f:
                    f.write(dockerfile_content)
                print(f"[INFO] Generated fallback Dockerfile")
            
            # Build the image
            if self.use_docker_lib:
                success = self._build_with_docker_lib(image_name, "Dockerfile", temp_dir)
            else:
                success = self._build_with_subprocess(image_name, dockerfile_path, temp_dir)
            
            return success
            
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"[WARNING] Failed to clean up temporary directory: {e}", file=sys.stderr)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Docker image from mission JSON")
    parser.add_argument('file', help='Path to mission JSON file')
    parser.add_argument(
        '--use-subprocess',
        action='store_true',
        help='Force use of subprocess instead of docker library'
    )
    
    args = parser.parse_args()
    
    try:
        builder = ImageBuilder(use_docker_lib=not args.use_subprocess)
        success = builder.build(args.file)
        
        if success:
            return 0
        else:
            return 1
            
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

