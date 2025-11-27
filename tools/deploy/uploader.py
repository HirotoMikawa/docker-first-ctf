"""
Project Sol: Mission Uploader (Ver 10.2)

Deploys draft mission JSON files to Supabase database.
Implements Phase 3.5: DB Deployment.

Uses Supabase client library.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Load environment variables
from dotenv import load_dotenv

# Supabase client
try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase library not installed. Run: pip install supabase", file=sys.stderr)
    sys.exit(1)

# Load .env file
load_dotenv()


class MissionUploader:
    """Deploys mission JSON files to Supabase database."""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_service_key: Optional[str] = None):
        """
        Initialize uploader.
        
        Args:
            supabase_url: Supabase URL (if None, reads from NEXT_PUBLIC_SUPABASE_URL or SUPABASE_URL env var)
            supabase_service_key: Supabase Service Key (if None, reads from SUPABASE_SERVICE_KEY env var)
        """
        # Get Supabase URL (try NEXT_PUBLIC_SUPABASE_URL first, then SUPABASE_URL)
        supabase_url = supabase_url or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
        if not supabase_url:
            raise ValueError(
                "Supabase URL not found. "
                "Please set NEXT_PUBLIC_SUPABASE_URL or SUPABASE_URL environment variable."
            )
        
        # Get Supabase Service Key
        supabase_service_key = supabase_service_key or os.getenv("SUPABASE_SERVICE_KEY")
        if not supabase_service_key:
            raise ValueError(
                "Supabase Service Key not found. "
                "Please set SUPABASE_SERVICE_KEY environment variable."
            )
        
        # Initialize Supabase client
        try:
            self.client = create_client(supabase_url, supabase_service_key)
        except Exception as e:
            raise RuntimeError(f"Failed to create Supabase client: {e}")
    
    def _map_json_to_db(self, mission_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map mission JSON to database column format.
        
        Mapping:
        - id: mission_id
        - title: Generated from narrative or type + difficulty
        - type: type
        - difficulty: difficulty
        - description: narrative.story_hook
        - metadata: Full JSON (as jsonb)
        - status: "active" (default, to make it playable immediately)
        
        Args:
            mission_json: Mission JSON dictionary
            
        Returns:
            Database record dictionary
        """
        mission_id = mission_json.get("mission_id", "")
        mission_type = mission_json.get("type", "")
        difficulty = mission_json.get("difficulty", 0)
        narrative = mission_json.get("narrative", {})
        story_hook = narrative.get("story_hook", "")
        environment = mission_json.get("environment", {})
        
        # Generate title from narrative or type + difficulty
        title = f"{mission_type} Challenge (Difficulty {difficulty})"
        if story_hook:
            # Use first sentence of story_hook as title if available
            first_sentence = story_hook.split('.')[0].strip()
            if first_sentence and len(first_sentence) < 100:
                title = first_sentence[:100]  # Limit to 100 chars
        
        # Extract additional fields from environment
        image_name = environment.get("image", "")
        internal_port = environment.get("internal_port", 8000)  # Default port
        points = environment.get("cost_token", 0)  # Use cost_token as points
        
        # Extract writeup from JSON (if present)
        writeup = mission_json.get("writeup", None)
        
        # Extract tags from JSON (if present)
        # Priority: top-level tags > environment.tags
        tags = mission_json.get("tags", None)
        if not tags and "environment" in mission_json:
            tags = mission_json["environment"].get("tags", None)
        
        # Build metadata (full JSON, but ensure tags are included if not in top-level)
        metadata = mission_json.copy()
        if tags and "tags" not in metadata:
            metadata["tags"] = tags
        
        # Build database record
        db_record = {
            "id": mission_id,  # Primary key
            "title": title,
            "description": story_hook,
            "difficulty": difficulty,
            "points": points,
            "image_name": image_name,
            "internal_port": internal_port,
            "metadata": metadata,  # Full JSON as jsonb (with tags included)
            "status": "active"  # Make it playable immediately
        }
        
        # Add writeup if present
        if writeup:
            db_record["writeup"] = writeup
        
        # Add optional fields if they exist in the JSON
        if "type" in mission_json:
            db_record["type"] = mission_json["type"]
        
        # Extract flag_answer (required field)
        # Priority: flag_answer > flag > generate default
        if "flag_answer" in mission_json and mission_json["flag_answer"]:
            db_record["flag_answer"] = mission_json["flag_answer"]
        elif "flag" in mission_json and mission_json["flag"]:
            db_record["flag_answer"] = mission_json["flag"]
        else:
            # Generate a default flag if missing (should not happen if drafter works correctly)
            import random
            import string
            random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            db_record["flag_answer"] = f"SolCTF{{{random_suffix}}}"
        
        return db_record
    
    def deploy(self, file_path: str, validate: bool = True) -> Dict[str, Any]:
        """
        Deploy mission JSON file to Supabase database.
        
        Args:
            file_path: Path to mission JSON file
            validate: Whether to validate the JSON before deploying (default: True)
            
        Returns:
            Dictionary with deployment result
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid
            RuntimeError: If database operation fails
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
        
        # Validate JSON structure (basic check)
        if validate:
            required_fields = ["mission_id", "type", "difficulty", "narrative", "environment"]
            for field in required_fields:
                if field not in mission_json:
                    raise ValueError(f"Missing required field in JSON: {field}")
        
        # Map JSON to database format
        db_record = self._map_json_to_db(mission_json)
        
        # Deploy to database using upsert (insert or update)
        try:
            mission_id = db_record["id"]
            
            # Use upsert: if record exists, update it; otherwise, insert it
            response = self.client.table("challenges").upsert(
                db_record,
                on_conflict="id"  # Use id as conflict key
            ).execute()
            
            if response.data:
                return {
                    "success": True,
                    "mission_id": mission_id,
                    "message": f"Mission '{mission_id}' deployed successfully",
                    "data": response.data[0] if isinstance(response.data, list) else response.data
                }
            else:
                raise RuntimeError("Upsert operation returned no data")
                
        except Exception as e:
            error_msg = str(e)
            
            # Check for common errors
            if "permission" in error_msg.lower() or "unauthorized" in error_msg.lower():
                raise RuntimeError(
                    "Database permission error. "
                    "Please check your SUPABASE_SERVICE_KEY has write permissions."
                )
            elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                raise RuntimeError(
                    "Database connection error. "
                    "Please check your SUPABASE_URL and network connection."
                )
            elif "column" in error_msg.lower() and "does not exist" in error_msg.lower():
                raise RuntimeError(
                    f"Database schema error: {error_msg}. "
                    "Please check if the challenges table has the required columns."
                )
            else:
                raise RuntimeError(f"Database operation failed: {error_msg}")
    
    def reset_database(self) -> Dict[str, Any]:
        """
        Reset database by deleting all records in correct order (child -> parent).
        
        Deletes in order:
        1. submission_logs (child table, references challenges)
        2. challenges (parent table)
        
        Returns:
            Dictionary with reset result
            
        Raises:
            RuntimeError: If database operation fails
        """
        try:
            deleted_logs_count = 0
            deleted_challenges_count = 0
            
            # Step 1: Delete submission_logs first (child table)
            try:
                # UUID形式のゼロ（Nil UUID）と比較することで、全件削除を行う
                logs_response = self.client.table("submission_logs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
                deleted_logs_count = len(logs_response.data) if logs_response.data else 0
            except Exception as e:
                # If submission_logs table doesn't exist, that's okay
                error_msg = str(e).lower()
                if "does not exist" not in error_msg and "relation" not in error_msg:
                    print(f"Warning: Failed to delete submission_logs: {e}", file=sys.stderr)
            
            # Step 2: Delete challenges (parent table)
            challenges_response = self.client.table("challenges").delete().neq("id", "").execute()
            deleted_challenges_count = len(challenges_response.data) if challenges_response.data else 0
            
            return {
                "success": True,
                "message": "Database cleared",
                "deleted_logs_count": deleted_logs_count,
                "deleted_challenges_count": deleted_challenges_count,
                "deleted_count": deleted_logs_count + deleted_challenges_count
            }
        except Exception as e:
            error_msg = str(e)
            raise RuntimeError(f"Database reset failed: {error_msg}")
    
    def reset_docker(self) -> Dict[str, Any]:
        """
        Reset Docker environment by removing all sol/mission- containers and images.
        
        Returns:
            Dictionary with reset result containing counts of removed containers and images
            
        Raises:
            RuntimeError: If Docker operation fails
        """
        removed_containers = 0
        removed_images = 0
        
        # Try to use docker library first
        try:
            import docker
            client = docker.from_env()
            
            # Find and remove containers
            all_containers = client.containers.list(all=True)
            container_ids_processed = set()
            
            for container in all_containers:
                # Check if container name or image contains sol/mission-
                container_name = container.name or ""
                container_image = str(container.image) if container.image else ""
                
                if "sol/mission-" in container_name or "sol/mission-" in container_image:
                    if container.id not in container_ids_processed:
                        try:
                            if container.status == "running":
                                container.stop(timeout=10)
                            container.remove()
                            removed_containers += 1
                            container_ids_processed.add(container.id)
                        except Exception as e:
                            print(f"Warning: Failed to remove container {container_name}: {e}", file=sys.stderr)
            
            # Find and remove images
            images = client.images.list()
            for image in images:
                # Check if any tag contains sol/mission-
                if image.tags:
                    for tag in image.tags:
                        if "sol/mission-" in tag:
                            try:
                                client.images.remove(image.id, force=True)
                                removed_images += 1
                                break  # Image already removed
                            except Exception as e:
                                print(f"Warning: Failed to remove image {tag}: {e}", file=sys.stderr)
            
            return {
                "success": True,
                "removed_containers": removed_containers,
                "removed_images": removed_images
            }
            
        except ImportError:
            # Fallback to subprocess
            import subprocess
            
            # Remove containers
            try:
                result = subprocess.run(
                    ["docker", "ps", "-a", "--format", "{{.ID}} {{.Names}} {{.Image}}"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                for line in result.stdout.strip().split('\n'):
                    if not line.strip():
                        continue
                    parts = line.split()
                    if len(parts) >= 3:
                        container_id = parts[0]
                        container_name = parts[1]
                        container_image = ' '.join(parts[2:])
                        
                        if "sol/mission-" in container_name or "sol/mission-" in container_image:
                            try:
                                # Stop if running
                                subprocess.run(
                                    ["docker", "stop", container_id],
                                    capture_output=True,
                                    check=False
                                )
                                # Remove
                                subprocess.run(
                                    ["docker", "rm", container_id],
                                    capture_output=True,
                                    check=False
                                )
                                removed_containers += 1
                            except Exception as e:
                                print(f"Warning: Failed to remove container {container_id}: {e}", file=sys.stderr)
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to list containers: {e}", file=sys.stderr)
            
            # Remove images
            try:
                result = subprocess.run(
                    ["docker", "images", "--format", "{{.Repository}}:{{.Tag}} {{.ID}}"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                for line in result.stdout.strip().split('\n'):
                    if not line.strip():
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        image_tag = parts[0]
                        image_id = parts[1]
                        
                        if "sol/mission-" in image_tag:
                            try:
                                subprocess.run(
                                    ["docker", "rmi", "-f", image_id],
                                    capture_output=True,
                                    check=False
                                )
                                removed_images += 1
                            except Exception as e:
                                print(f"Warning: Failed to remove image {image_tag}: {e}", file=sys.stderr)
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to list images: {e}", file=sys.stderr)
            
            return {
                "success": True,
                "removed_containers": removed_containers,
                "removed_images": removed_images
            }
        except Exception as e:
            raise RuntimeError(f"Docker reset failed: {str(e)}")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy mission JSON to Supabase database")
    parser.add_argument('file', help='Path to mission JSON file')
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip JSON validation before deploying'
    )
    parser.add_argument(
        '--supabase-url',
        type=str,
        default=None,
        help='Supabase URL (if not set, reads from env var)'
    )
    parser.add_argument(
        '--supabase-service-key',
        type=str,
        default=None,
        help='Supabase Service Key (if not set, reads from env var)'
    )
    
    args = parser.parse_args()
    
    try:
        uploader = MissionUploader(
            supabase_url=args.supabase_url,
            supabase_service_key=args.supabase_service_key
        )
        result = uploader.deploy(args.file, validate=not args.no_validate)
        
        print(f"✓ {result['message']}")
        print(f"  Mission ID: {result['mission_id']}")
        return 0
        
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

