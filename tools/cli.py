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
from generation.drafter import MissionDrafter
from deploy.uploader import MissionUploader
from builder.simple_builder import ImageBuilder
import json


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
        success, file_path, mission = drafter.draft(
            difficulty=difficulty,
            max_retries=max_retries,
            verbose=verbose
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


def cmd_auto_add(args):
    """Automated mission addition: draft -> deploy -> build -> generate SNS."""
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
    
    try:
        # Step 1: Draft Generation
        print("[1/4] Generating draft mission JSON...")
        drafter = MissionDrafter(output_dir=output_dir, api_key=api_key)
        success, draft_file_path, mission = drafter.draft(
            difficulty=difficulty,
            max_retries=3,
            verbose=verbose
        )
        
        if not success:
            print("[ERROR] Draft generation failed", file=sys.stderr)
            return 1
        
        mission_id = mission.get("mission_id", "UNKNOWN")
        print(f"[1/4] ✓ Draft generated: {draft_file_path}")
        print(f"      Mission ID: {mission_id}")
        print("")
        
        # Step 2: Deploy to Database
        print("[2/4] Deploying to database...")
        uploader = MissionUploader(
            supabase_url=supabase_url,
            supabase_service_key=supabase_service_key
        )
        deploy_result = uploader.deploy(draft_file_path, validate=True)
        
        print(f"[2/4] ✓ Deployed to Database")
        print(f"      Mission ID: {deploy_result['mission_id']}")
        print("")
        
        # Step 3: Build Docker Image
        print("[3/4] Building Docker image...")
        builder = ImageBuilder(use_docker_lib=not use_subprocess)
        build_success = builder.build(draft_file_path)
        
        if not build_success:
            print("[ERROR] Docker image build failed", file=sys.stderr)
            print("[WARNING] Mission is deployed to database but image build failed", file=sys.stderr)
            return 1
        
        print(f"[3/4] ✓ Docker Image Built")
        print("")
        
        # Step 4: Generate SNS Content
        print("[4/4] Generating SNS marketing content...")
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
        
        print(f"[4/4] ✓ SNS Content Generated")
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
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


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
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

