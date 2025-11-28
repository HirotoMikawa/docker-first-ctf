#!/usr/bin/env python3
"""
Project Sol: CLI Tool (Ver 10.2)

Unified CLI interface for automation tools:
- validate: Validate mission JSON against SSOT
- generate: Generate marketing content

Usage:
    python tools/cli.py validate <mission_json_file>
    python tools/cli.py generate <mission_json_file> <sns|briefing> [base_url]
"""

import sys
import argparse
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ci.validator import validate_mission_file, ValidationError
from marketing.generator import generate_from_file, ContentGenerator
from generation.drafter import MissionDrafter, CHALLENGE_CATEGORIES, VISUAL_THEMES
from deploy.uploader import MissionUploader
from builder.simple_builder import ImageBuilder
from solver.container_tester import ContainerTester
import json

# Docker library for cleanup
try:
    import docker
except ImportError:
    docker = None

# Requests library (optional, for flag verification)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def cmd_validate(args):
    """Validate mission JSON file."""
    file_path = args.file
    
    try:
        is_valid, errors, warnings = validate_mission_file(file_path)
        
        if warnings:
            print("Warnings:", file=sys.stderr)
            for warning in warnings:
                print(f"  ⚠ {warning}", file=sys.stderr)
            print(file=sys.stderr)
        
        if errors:
            print("Errors:", file=sys.stderr)
            for error in errors:
                print(f"  ✗ {error}", file=sys.stderr)
            print(file=sys.stderr)
            print("Validation FAILED", file=sys.stderr)
            return 1
        else:
            print("✓ Validation PASSED", file=sys.stdout)
            if warnings:
                print(f"  ({len(warnings)} warning(s))", file=sys.stdout)
            return 0
    
    except ValidationError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_generate(args):
    """Generate marketing content using OpenAI API."""
    file_path = args.file
    output_format = args.format
    base_url = args.base_url
    api_key = args.api_key
    use_ai = not args.no_ai  # --no-ai が指定されていれば False
    
    try:
        content = generate_from_file(
            file_path, 
            output_format, 
            base_url, 
            api_key=api_key,
            use_ai=use_ai if output_format == "sns" else False
        )
        print(content)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_draft(args):
    """Generate draft mission JSON using OpenAI API."""
    difficulty = args.difficulty
    output_dir = args.output_dir
    verbose = args.verbose
    api_key = args.api_key
    max_retries = args.max_retries
    
    try:
        drafter = MissionDrafter(output_dir=output_dir, api_key=api_key)
        category = getattr(args, 'category', None)
        theme = getattr(args, 'theme', None)
        success, file_path, mission = drafter.draft(
            difficulty=difficulty,
            max_retries=max_retries,
            verbose=verbose,
            category=category,
            theme=theme
        )
        
        if success:
            print(f"✓ Draft generated successfully: {file_path}")
            print(f"  Mission ID: {mission['mission_id']}")
            print(f"  Type: {mission['type']}")
            print(f"  Difficulty: {mission['difficulty']}")
            return 0
        else:
            print("✗ Failed to generate valid draft after multiple attempts", file=sys.stderr)
            print("  Try running with --verbose to see validation errors", file=sys.stderr)
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


def cmd_deploy(args):
    """Deploy mission JSON to Supabase database."""
    file_path = args.file
    no_validate = args.no_validate
    supabase_url = args.supabase_url
    supabase_service_key = args.supabase_service_key
    
    try:
        uploader = MissionUploader(
            supabase_url=supabase_url,
            supabase_service_key=supabase_service_key
        )
        result = uploader.deploy(file_path, validate=not no_validate)
        
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


def cmd_build(args):
    """Build Docker image from mission JSON."""
    file_path = args.file
    use_subprocess = args.use_subprocess
    
    try:
        builder = ImageBuilder(use_docker_lib=not use_subprocess)
        success = builder.build(file_path)
        
        if success:
            print("✓ Image build completed successfully")
            return 0
        else:
            print("✗ Image build failed", file=sys.stderr)
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


def cmd_reset(args):
    """Reset development environment: clear database and remove Docker containers/images."""
    supabase_url = args.supabase_url
    supabase_service_key = args.supabase_service_key
    
    # Confirmation prompt
    print("⚠️  WARNING: This will delete ALL data from the database and remove ALL sol/mission- containers and images.")
    print("")
    response = input("Are you sure you want to proceed? [y/N]: ").strip().lower()
    
    if response != 'y':
        print("Reset cancelled.")
        return 0
    
    print("")
    print("[RESET] Starting environment reset...")
    print("")
    
    try:
        # Step 1: Reset Database
        print("[1/2] Resetting database...")
        uploader = MissionUploader(
            supabase_url=supabase_url,
            supabase_service_key=supabase_service_key
        )
        db_result = uploader.reset_database()
        print(f"[DELETE] {db_result['message']}.")
        if db_result.get('deleted_logs_count', 0) > 0:
            print(f"         Removed {db_result['deleted_logs_count']} submission log(s).")
        if db_result.get('deleted_challenges_count', 0) > 0:
            print(f"         Removed {db_result['deleted_challenges_count']} challenge(s).")
        if db_result.get('deleted_count', 0) > 0:
            print(f"         Total: {db_result['deleted_count']} record(s) removed.")
        print("")
        
        # Step 2: Reset Docker
        print("[2/2] Resetting Docker environment...")
        docker_result = uploader.reset_docker()
        print(f"[DELETE] Removed {docker_result['removed_containers']} container(s).")
        print(f"[DELETE] Removed {docker_result['removed_images']} image(s).")
        print("")
        
        print("[SUCCESS] Environment is clean.")
        return 0
        
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_auto_add(args):
    """Automated mission addition: draft -> build -> test -> regenerate writeup -> deploy -> generate SNS."""
    difficulty = args.difficulty
    output_dir = args.output_dir
    api_key = args.api_key
    supabase_url = args.supabase_url
    supabase_service_key = args.supabase_service_key
    base_url = args.base_url
    use_subprocess = args.use_subprocess
    verbose = args.verbose
    
    print("[INFO] Starting auto-generation sequence...")
    print("")
    
    mission_id = None
    draft_file_path = None
    container_id = None
    container_url = None
    tester = None
    
    try:
        # Step 1: Draft Generation (without writeup initially)
        print("[1/6] Generating draft mission JSON (without writeup)...")
        drafter = MissionDrafter(output_dir=output_dir, api_key=api_key)
        # Use random category and theme for auto-add (for diversity)
        success, draft_file_path, mission = drafter.draft(
            difficulty=difficulty,
            max_retries=3,
            verbose=verbose,
            category=None,  # Random selection for diversity
            theme=None,  # Random selection for diversity
        )
        
        if not success:
            print("[ERROR] Draft generation failed", file=sys.stderr)
            return 1
        
        mission_id = mission.get("mission_id", "UNKNOWN")
        print(f"[1/8] ✓ Draft generated: {draft_file_path}")
        print(f"      Mission ID: {mission_id}")
        print("")
        
        # Step 2: Validate Dockerfile (user creation check + flag placement)
        print("[2/8] Validating Dockerfile...")
        try:
            with open(draft_file_path, 'r', encoding='utf-8') as f:
                mission_data = json.load(f)
            dockerfile_content = mission_data.get("files", {}).get("Dockerfile", "")
            problem_type = mission_data.get("type", "Unknown")
            expected_flag = mission_data.get("flag_answer", "")
            
            if dockerfile_content:
                # Check user creation
                from validation.dockerfile_validator import validate_dockerfile_user_creation
                is_valid, errors = validate_dockerfile_user_creation(dockerfile_content)
                if not is_valid:
                    print("[WARNING] Dockerfile validation issues found:", file=sys.stderr)
                    for error in errors:
                        print(f"  ⚠ {error}", file=sys.stderr)
                    print("[WARNING] Continuing with build, but container may fail to start", file=sys.stderr)
                
                # Check flag placement
                from validation.flag_placement_validator import validate_flag_placement
                is_flag_valid, flag_errors = validate_flag_placement(dockerfile_content, problem_type, expected_flag)
                if not is_flag_valid:
                    print("[WARNING] Flag placement validation issues found:", file=sys.stderr)
                    for error in flag_errors:
                        print(f"  ⚠ {error}", file=sys.stderr)
                    print("[WARNING] Flag may be in wrong location. Problem may still work, but not optimal.", file=sys.stderr)
        except Exception as e:
            print(f"[WARNING] Dockerfile validation skipped: {e}", file=sys.stderr)
        print("")
        
        # Step 3: Build Docker Image
        print("[3/8] Building Docker image...")
        builder = ImageBuilder(use_docker_lib=not use_subprocess)
        build_success = builder.build(draft_file_path)
        
        if not build_success:
            print("[ERROR] Docker image build failed", file=sys.stderr)
            return 1
        
        print(f"[3/8] ✓ Docker Image Built")
        print("")
        
        # Step 4: Start Test Container and Verify Solvability
        print("[4/8] Starting test container and verifying solvability...")
        tester = ContainerTester(use_docker_lib=not use_subprocess)
        
        image_name = mission.get("environment", {}).get("image", "")
        flag_answer = mission.get("flag_answer", "")
        
        if not image_name:
            print("[ERROR] Missing image name in mission JSON", file=sys.stderr)
            return 1
        
        if not flag_answer:
            print("[ERROR] Missing flag_answer in mission JSON", file=sys.stderr)
            return 1
        
        # Start test container
        container_id, port, container_url = tester.start_test_container(
            image_name=image_name,
            flag=flag_answer,
            timeout=30
        )
        
        if not container_id or not container_url:
            print("[ERROR] Failed to start test container", file=sys.stderr)
            # Mark as unsolvable
            mission["writeup"] = """# ⚠️ 問題の不備について

この問題には不備があり、現在解答できない可能性があります。

**問題の状態:**
- コンテナの起動に失敗しました
- 解答の確認ができませんでした

**推奨事項:**
- 問題のコードを確認してください
- Dockerfileとアプリケーションコードに問題がないか確認してください
- 必要に応じて問題を再生成してください。

この問題は、修正が必要な状態です。"""
            # Save updated JSON
            with open(draft_file_path, 'w', encoding='utf-8') as f:
                json.dump(mission, f, indent=2, ensure_ascii=False)
            print("[WARNING] Mission marked as potentially unsolvable", file=sys.stderr)
        else:
            print(f"[4/8] ✓ Test container started")
            print(f"      Container ID: {container_id[:12]}")
            print(f"      Container URL: {container_url}")
            print("")
            
            # Test solvability using internal inspection + functional testing
            mission_type = mission.get("type", "Web")
            is_solvable, error_msg, found_flag = tester.test_solvability(
                container_id=container_id,
                expected_flag=flag_answer,
                timeout=60,
                mission_type=mission_type,
                container_url=container_url
            )
            
            if not is_solvable:
                print(f"[ERROR] Problem is NOT solvable: {error_msg}", file=sys.stderr)
                print(f"[ERROR] This problem needs to be fixed or regenerated", file=sys.stderr)
                # Mark as unsolvable and stop deployment
                mission["writeup"] = f"""# ⚠️ 問題の不備について

この問題には不備があり、**実際に解答できません**。

**問題の状態:**
- コンテナは起動しましたが、自動検証で解答できませんでした
- エラー: {error_msg}
- **この問題はデプロイされません**

**推奨事項:**
- 問題のコードを確認してください
- フラグが正しく配置されているか確認してください
- 解く側が実際にアクセスできる情報で解答できるか確認してください
- 問題を再生成してください。

この問題は、修正が必要な状態です。"""
                # Save updated JSON
                with open(draft_file_path, 'w', encoding='utf-8') as f:
                    json.dump(mission, f, indent=2, ensure_ascii=False)
                print("[ERROR] Mission marked as unsolvable - deployment will be skipped", file=sys.stderr)
                # Stop the process - don't deploy unsolvable problems
                tester.stop_test_container(container_id)
                return 1
            else:
                print(f"[4/8] ✓ Container is solvable")
                if found_flag:
                    print(f"      Flag found: {found_flag}")
                print("")
                
                # Step 5: Verify flag can be obtained (optional check)
                print("[5/8] Verifying flag accessibility...")
                # Try to find flag in the container
                flag_found = False
                flag_location = None
                if HAS_REQUESTS:
                    try:
                        import requests
                        # Check common locations
                        test_paths = [
                            ("/", "root"),
                            ("/flag", "flag endpoint"),
                            ("/api/flag", "api flag endpoint"),
                            ("/debug", "debug endpoint"),
                        ]
                        for path, desc in test_paths:
                            try:
                                res = requests.get(f"{container_url}{path}", timeout=3)
                                if res.status_code == 200 and flag_answer in res.text:
                                    flag_found = True
                                    flag_location = f"{path} ({desc})"
                                    print(f"      ✓ Flag found at: {flag_location}")
                                    break
                            except:
                                pass
                        if not flag_found:
                            print(f"      ⚠ Flag not found in common locations (this is normal for RCE/SSRF challenges)")
                    except Exception as e:
                        print(f"      ⚠ Flag verification skipped: {e}")
                
                # Step 6: Regenerate Writeup with Actual Container URL
                print("[6/8] Regenerating writeup with actual container URL...")
                new_writeup = drafter.regenerate_writeup(
                    mission_json=mission,
                    container_url=container_url,
                    api_key=api_key
                )
                
                if new_writeup:
                    mission["writeup"] = new_writeup
                    # Save updated JSON
                    with open(draft_file_path, 'w', encoding='utf-8') as f:
                        json.dump(mission, f, indent=2, ensure_ascii=False)
                    print(f"[6/8] ✓ Writeup regenerated with actual container URL")
                    print("")
                else:
                    print("[WARNING] Failed to regenerate writeup, using original", file=sys.stderr)
                    print("")
        
        # Step 7: Deploy to Database
        print("[7/8] Deploying to database...")
        try:
            uploader = MissionUploader(
                supabase_url=supabase_url,
                supabase_service_key=supabase_service_key
            )
            deploy_result = uploader.deploy(draft_file_path, validate=True)
            
            print(f"[7/8] ✓ Deployed to Database")
            print(f"      Mission ID: {deploy_result['mission_id']}")
            print("")
        except Exception as deploy_error:
            print(f"[ERROR] Database deployment failed: {deploy_error}", file=sys.stderr)
            print("[WARNING] Mission JSON file is saved but not deployed to database", file=sys.stderr)
            if draft_file_path:
                print(f"[INFO] You can manually deploy later using: python tools/cli.py deploy {draft_file_path}", file=sys.stderr)
            raise  # Re-raise to trigger cleanup
        
        # Step 7: Generate SNS Content
        print("[8/8] Generating SNS marketing content...")
        sns_content = generate_from_file(
            draft_file_path,
            output_format="sns",
            base_url=base_url,
            api_key=api_key,
            use_ai=True
        )
        
        # Save SNS content to file
        sns_file_path = Path(draft_file_path).parent / f"{mission_id}_sns.txt"
        with open(sns_file_path, 'w', encoding='utf-8') as f:
            f.write(sns_content)
        
        print(f"[8/8] ✓ SNS Content Generated")
        print(f"      Saved to: {sns_file_path}")
        print("")
        
        # Display SNS content
        print("=" * 60)
        print("Generated SNS Post:")
        print("=" * 60)
        print(sns_content)
        print("=" * 60)
        print("")
        
        # Success message
        print(f"[SUCCESS] Mission {mission_id} is live!")
        print(f"  - Draft: {draft_file_path}")
        print(f"  - Database: Deployed")
        print(f"  - Docker Image: Built")
        if container_url:
            print(f"  - Test Container URL: {container_url}")
        print(f"  - SNS Content: {sns_file_path}")
        
        return 0
        
    except ValueError as e:
        print(f"[ERROR] Validation error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"[ERROR] Runtime error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"[ERROR] File not found: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[ERROR] Operation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Clean up test container in all cases (success or failure)
        if container_id and tester:
            try:
                print("[CLEANUP] Stopping test container...")
                tester.stop_test_container(container_id)
                print("[CLEANUP] ✓ Test container stopped")
            except Exception as cleanup_error:
                print(f"[WARNING] Failed to cleanup test container: {cleanup_error}", file=sys.stderr)
                # Try to force remove container
                try:
                    if tester.use_docker_lib and docker:
                        container = tester.client.containers.get(container_id)
                        container.remove(force=True)
                    else:
                        import subprocess
                        subprocess.run(["docker", "rm", "-f", container_id], 
                                     capture_output=True, timeout=10)
                    print("[CLEANUP] ✓ Test container force-removed")
                except Exception as force_cleanup_error:
                    print(f"[WARNING] Failed to force-remove container: {force_cleanup_error}", file=sys.stderr)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Project Sol Automation Tools (Ver 10.2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate mission JSON
  python tools/cli.py validate challenges/samples/valid_mission.json
  
  # Generate draft mission JSON
  python tools/cli.py draft
  
  # Build Docker image from mission JSON
  python tools/cli.py build challenges/drafts/SOL-MSN-XXXX.json
  
  # Deploy mission JSON to database
  python tools/cli.py deploy challenges/drafts/SOL-MSN-XXXX.json
  
  # Generate SNS teaser
  python tools/cli.py generate challenges/samples/valid_mission.json sns
  
  # Generate mission briefing
  python tools/cli.py generate challenges/samples/valid_mission.json briefing
  
  # Reset development environment
  python tools/cli.py reset
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # validate command
    parser_validate = subparsers.add_parser('validate', help='Validate mission JSON against SSOT')
    parser_validate.add_argument('file', help='Path to mission JSON file')
    
    # draft command
    parser_draft = subparsers.add_parser('draft', help='Generate draft mission JSON using OpenAI API')
    parser_draft.add_argument(
        '--difficulty',
        type=int,
        choices=[1, 2, 3, 4, 5],
        default=None,
        help='Target difficulty (1-5). If not specified, random.'
    )
    parser_draft.add_argument(
        '--output-dir',
        type=str,
        default='challenges/drafts',
        help='Output directory for drafts (default: challenges/drafts)'
    )
    parser_draft.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='OpenAI API key (if not set, reads from OPENAI_API_KEY env var)'
    )
    parser_draft.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts if validation fails (default: 3)'
    )
    parser_draft.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed error messages for debugging'
    )
    parser_draft.add_argument(
        '--category',
        type=str,
        choices=list(CHALLENGE_CATEGORIES.keys()),
        default=None,
        help='Challenge category (e.g., WEB_SQLI, CRYPTO_RSA). If not specified, random.'
    )
    parser_draft.add_argument(
        '--theme',
        type=str,
        choices=VISUAL_THEMES,
        default=None,
        help='Visual theme (e.g., CORPORATE, UNDERGROUND). If not specified, random.'
    )
    
    # build command
    parser_build = subparsers.add_parser('build', help='Build Docker image from mission JSON')
    parser_build.add_argument('file', help='Path to mission JSON file')
    parser_build.add_argument(
        '--use-subprocess',
        action='store_true',
        help='Force use of subprocess instead of docker library'
    )
    
    # deploy command
    parser_deploy = subparsers.add_parser('deploy', help='Deploy mission JSON to Supabase database')
    parser_deploy.add_argument('file', help='Path to mission JSON file')
    parser_deploy.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip JSON validation before deploying'
    )
    parser_deploy.add_argument(
        '--supabase-url',
        type=str,
        default=None,
        help='Supabase URL (if not set, reads from NEXT_PUBLIC_SUPABASE_URL or SUPABASE_URL env var)'
    )
    parser_deploy.add_argument(
        '--supabase-service-key',
        type=str,
        default=None,
        help='Supabase Service Key (if not set, reads from SUPABASE_SERVICE_KEY env var)'
    )
    
    # reset command
    parser_reset = subparsers.add_parser('reset', help='Reset development environment: clear database and remove Docker containers/images')
    parser_reset.add_argument(
        '--supabase-url',
        type=str,
        default=None,
        help='Supabase URL (if not set, reads from NEXT_PUBLIC_SUPABASE_URL or SUPABASE_URL env var)'
    )
    parser_reset.add_argument(
        '--supabase-service-key',
        type=str,
        default=None,
        help='Supabase Service Key (if not set, reads from SUPABASE_SERVICE_KEY env var)'
    )
    
    # auto-add command
    parser_auto_add = subparsers.add_parser('auto-add', help='Automated mission addition: draft -> deploy -> build -> generate SNS')
    parser_auto_add.add_argument(
        '--difficulty',
        type=int,
        choices=[1, 2, 3, 4, 5],
        default=None,
        help='Target difficulty (1-5). If not specified, random.'
    )
    parser_auto_add.add_argument(
        '--output-dir',
        type=str,
        default='challenges/drafts',
        help='Output directory for drafts (default: challenges/drafts)'
    )
    parser_auto_add.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='OpenAI API key (if not set, reads from OPENAI_API_KEY env var)'
    )
    parser_auto_add.add_argument(
        '--supabase-url',
        type=str,
        default=None,
        help='Supabase URL (if not set, reads from NEXT_PUBLIC_SUPABASE_URL or SUPABASE_URL env var)'
    )
    parser_auto_add.add_argument(
        '--supabase-service-key',
        type=str,
        default=None,
        help='Supabase Service Key (if not set, reads from SUPABASE_SERVICE_KEY env var)'
    )
    parser_auto_add.add_argument(
        '--base-url',
        type=str,
        default=None,
        help='Base URL for mission links (optional, for SNS generation)'
    )
    parser_auto_add.add_argument(
        '--use-subprocess',
        action='store_true',
        help='Force use of subprocess for Docker build instead of docker library'
    )
    parser_auto_add.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed error messages for debugging'
    )
    
    # generate command
    parser_generate = subparsers.add_parser('generate', help='Generate marketing content using OpenAI API')
    parser_generate.add_argument('file', help='Path to mission JSON file')
    parser_generate.add_argument(
        'format',
        choices=['sns', 'briefing'],
        help='Output format: sns (SNS teaser with AI) or briefing (Mission briefing)'
    )
    parser_generate.add_argument(
        'base_url',
        nargs='?',
        default=None,
        help='Base URL for mission links (optional, for sns format)'
    )
    parser_generate.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='OpenAI API key (if not set, reads from OPENAI_API_KEY env var)'
    )
    parser_generate.add_argument(
        '--no-ai',
        action='store_true',
        help='Disable AI generation and use fallback template (for sns format)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'generate':
        return cmd_generate(args)
    elif args.command == 'draft':
        return cmd_draft(args)
    elif args.command == 'build':
        return cmd_build(args)
    elif args.command == 'deploy':
        return cmd_deploy(args)
    elif args.command == 'auto-add':
        return cmd_auto_add(args)
    elif args.command == 'reset':
        return cmd_reset(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

