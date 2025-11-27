"""
Project Sol: Mission Validator (Ver 10.2)

Validates mission JSON against SSOT specifications:
- PROJECT_MASTER.md: JSON Schema, Security Standards
- DIFFICULTY_SPEC.md: Difficulty Formula, Consistency Rules
- CONTENT_PLAN.md: Forbidden Words

Uses only Python standard library.
"""

import json
import re
import sys
from typing import Dict, List, Tuple, Any
from pathlib import Path


# Forbidden Words (CONTENT_PLAN.md SSOT)
FORBIDDEN_WORDS = [
    "Great", "Good luck", "Happy", "Sorry", "Please", 
    "I think", "Feel", "Hope"
]
FORBIDDEN_PUNCTUATION = "!"

# Allowed types (PROJECT_MASTER.md)
ALLOWED_TYPES = ["RCE", "SQLi", "SSRF", "XXE", "IDOR", "PrivEsc", "LogicError", "Misconfig"]

# Allowed statuses (PROJECT_MASTER.md)
ALLOWED_STATUSES = ["draft", "active", "inactive", "deprecated"]

# Disallowed CVE Types (PROJECT_MASTER.md)
DISALLOWED_CVE_TYPES = [
    "Kernel-level RCE",
    "Privileged Container",
    "Docker Socket Access",
    "Host Resource Dependency"
]

# Base images (PROJECT_MASTER.md)
ALLOWED_BASE_IMAGES = ["python:3.11-slim", "alpine:3.19"]


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class MissionValidator:
    """Validates mission JSON against SSOT specifications."""
    
    def __init__(self, mission_data: Dict[str, Any]):
        self.mission = mission_data
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validation checks.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        # Schema validation
        self._validate_schema()
        
        # Difficulty calculation validation
        self._validate_difficulty()
        
        # Forbidden words check
        self._validate_forbidden_words()
        
        # Security standards check
        self._validate_security_standards()
        
        # Additional consistency checks
        self._validate_consistency()
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _validate_schema(self):
        """Validate JSON Schema (PROJECT_MASTER.md Section 4)."""
        required_fields = [
            "mission_id", "mission_version", "type", "difficulty",
            "difficulty_factors", "vulnerability", "environment", 
            "narrative", "status"
        ]
        
        for field in required_fields:
            if field not in self.mission:
                self.errors.append(f"Missing required field: {field}")
        
        # mission_id format: SOL-MSN-XXX
        if "mission_id" in self.mission:
            mission_id = self.mission["mission_id"]
            if not re.match(r"^SOL-MSN-[A-Z0-9]+$", mission_id):
                self.errors.append(
                    f"mission_id must match pattern 'SOL-MSN-XXX': {mission_id}"
                )
        
        # mission_version: SemVer
        if "mission_version" in self.mission:
            version = self.mission["mission_version"]
            if not re.match(r"^\d+\.\d+\.\d+$", version):
                self.errors.append(
                    f"mission_version must be SemVer (MAJOR.MINOR.PATCH): {version}"
                )
        
        # type: Allowed values
        if "type" in self.mission:
            mission_type = self.mission["type"]
            if mission_type not in ALLOWED_TYPES:
                self.errors.append(
                    f"type must be one of {ALLOWED_TYPES}: {mission_type}"
                )
        
        # status: Allowed values
        if "status" in self.mission:
            status = self.mission["status"]
            if status not in ALLOWED_STATUSES:
                self.errors.append(
                    f"status must be one of {ALLOWED_STATUSES}: {status}"
                )
        
        # difficulty_factors structure
        if "difficulty_factors" in self.mission:
            factors = self.mission["difficulty_factors"]
            required_factors = ["tech", "read", "explore"]
            for factor in required_factors:
                if factor not in factors:
                    self.errors.append(f"Missing difficulty_factor: {factor}")
                else:
                    value = factors[factor]
                    if not isinstance(value, int) or value < 1 or value > 5:
                        self.errors.append(
                            f"difficulty_factors.{factor} must be integer 1-5: {value}"
                        )
        
        # vulnerability structure
        if "vulnerability" in self.mission:
            vuln = self.mission["vulnerability"]
            required_vuln_fields = ["cve_id", "cvss", "attack_vector"]
            for field in required_vuln_fields:
                if field not in vuln:
                    self.errors.append(f"Missing vulnerability field: {field}")
            
            # CVE ID format
            if "cve_id" in vuln:
                cve_id = vuln["cve_id"]
                if not re.match(r"^CVE-\d{4}-\d{4,}$", cve_id):
                    self.warnings.append(
                        f"CVE ID format may be invalid: {cve_id}"
                    )
            
            # CVSS range
            if "cvss" in vuln:
                cvss = vuln["cvss"]
                if not isinstance(cvss, (int, float)) or cvss < 0.0 or cvss > 10.0:
                    self.errors.append(
                        f"cvss must be number 0.0-10.0: {cvss}"
                    )
        
        # environment structure
        if "environment" in self.mission:
            env = self.mission["environment"]
            required_env_fields = ["image", "base_image", "cost_token", "expected_solve_time", "tags"]
            for field in required_env_fields:
                if field not in env:
                    self.errors.append(f"Missing environment field: {field}")
            
            # base_image: Allowed values
            if "base_image" in env:
                base_image = env["base_image"]
                if base_image not in ALLOWED_BASE_IMAGES:
                    self.warnings.append(
                        f"base_image should be one of {ALLOWED_BASE_IMAGES}: {base_image}"
                    )
            
            # cost_token: Range 1000-10000
            if "cost_token" in env:
                cost = env["cost_token"]
                if not isinstance(cost, int) or cost < 1000 or cost > 10000:
                    self.errors.append(
                        f"cost_token must be integer 1000-10000: {cost}"
                    )
            
            # expected_solve_time: Regex ^[0-9]+m$
            if "expected_solve_time" in env:
                solve_time = env["expected_solve_time"]
                if not re.match(r"^[0-9]+m$", solve_time):
                    self.errors.append(
                        f"expected_solve_time must match pattern '^[0-9]+m$': {solve_time}"
                    )
            
            # tags: Array
            if "tags" in env:
                tags = env["tags"]
                if not isinstance(tags, list):
                    self.errors.append(f"tags must be array: {tags}")
        
        # narrative structure
        if "narrative" in self.mission:
            narrative = self.mission["narrative"]
            required_narrative_fields = ["story_hook", "tone"]
            for field in required_narrative_fields:
                if field not in narrative:
                    self.errors.append(f"Missing narrative field: {field}")
            
            # story_hook: Max 3 sentences
            if "story_hook" in narrative:
                story_hook = narrative["story_hook"]
                if not isinstance(story_hook, str):
                    self.errors.append("story_hook must be string")
                else:
                    # Split by sentence endings, but avoid splitting on IP addresses and decimals
                    # Use lookahead to ensure we're not in the middle of an IP address or number
                    sentences = re.split(r'(?<!\d)[.!?]+(?!\d)\s*', story_hook)
                    sentences = [s.strip() for s in sentences if s.strip()]
                    if len(sentences) > 3:
                        self.errors.append(
                            f"story_hook must be max 3 sentences: {len(sentences)} sentences found"
                        )
            
            # tone: Must be "combat"
            if "tone" in narrative:
                tone = narrative["tone"]
                if tone != "combat":
                    self.errors.append(f"tone must be 'combat': {tone}")
        
        # difficulty: Integer 1-5
        if "difficulty" in self.mission:
            difficulty = self.mission["difficulty"]
            if not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
                self.errors.append(
                    f"difficulty must be integer 1-5: {difficulty}"
                )
    
    def _validate_difficulty(self):
        """Validate difficulty calculation (DIFFICULTY_SPEC.md Section 1)."""
        if "difficulty" not in self.mission or "difficulty_factors" not in self.mission:
            return  # Already reported in schema validation
        
        difficulty = self.mission["difficulty"]
        factors = self.mission["difficulty_factors"]
        
        if "tech" not in factors or "read" not in factors or "explore" not in factors:
            return  # Already reported in schema validation
        
        tech = factors["tech"]
        read = factors["read"]
        explore = factors["explore"]
        
        # Formula: Difficulty = Clamp(Round(Tech * 0.4 + Read * 0.2 + Explore * 0.4), 1, 5)
        calculated = round(tech * 0.4 + read * 0.2 + explore * 0.4)
        calculated = max(1, min(5, calculated))  # Clamp to 1-5
        
        if calculated != difficulty:
            self.errors.append(
                f"difficulty calculation mismatch: "
                f"expected {calculated} (from factors tech={tech}, read={read}, explore={explore}), "
                f"got {difficulty}"
            )
        
        # Consistency Rules (DIFFICULTY_SPEC.md Section 3)
        if difficulty == 1:
            if tech > 2 or explore > 2:
                self.warnings.append(
                    f"Difficulty 1 consistency: tech should be <= 2, explore should be <= 2 "
                    f"(got tech={tech}, explore={explore})"
                )
        elif difficulty == 2:
            if not (2 <= tech <= 3) or not (2 <= explore <= 3):
                self.warnings.append(
                    f"Difficulty 2 consistency: tech should be 2-3, explore should be 2-3 "
                    f"(got tech={tech}, explore={explore})"
                )
        elif difficulty == 3:
            if not (3 <= tech <= 4) or not (3 <= explore <= 4):
                self.warnings.append(
                    f"Difficulty 3 consistency: tech should be 3-4, explore should be 3-4 "
                    f"(got tech={tech}, explore={explore})"
                )
        elif difficulty == 4:
            if tech != 4 or explore != 4:
                self.warnings.append(
                    f"Difficulty 4 consistency: tech should be 4, explore should be 4 "
                    f"(got tech={tech}, explore={explore})"
                )
        elif difficulty == 5:
            if tech < 4 or explore < 4:
                self.warnings.append(
                    f"Difficulty 5 consistency: tech should be >= 4, explore should be >= 4 "
                    f"(got tech={tech}, explore={explore})"
                )
    
    def _validate_forbidden_words(self):
        """Validate Forbidden Words (CONTENT_PLAN.md Section 1)."""
        if "narrative" not in self.mission or "story_hook" not in self.mission["narrative"]:
            return  # Already reported in schema validation
        
        story_hook = self.mission["narrative"]["story_hook"]
        if not isinstance(story_hook, str):
            return
        
        story_hook_lower = story_hook.lower()
        
        # Check forbidden words
        for word in FORBIDDEN_WORDS:
            if word.lower() in story_hook_lower:
                self.errors.append(
                    f"Forbidden word found in story_hook: '{word}'"
                )
        
        # Check forbidden punctuation
        if FORBIDDEN_PUNCTUATION in story_hook:
            self.errors.append(
                f"Forbidden punctuation found in story_hook: '{FORBIDDEN_PUNCTUATION}'"
            )
    
    def _validate_security_standards(self):
        """Validate Security Standards (PROJECT_MASTER.md Section 5)."""
        # Check for disallowed CVE types (would need CVE database lookup in real implementation)
        # For now, we check if the type suggests a disallowed category
        if "type" in self.mission:
            mission_type = self.mission["type"]
            if mission_type == "RCE":
                # Check if it's a kernel-level RCE (would need CVE database)
                self.warnings.append(
                    "RCE type detected: Ensure this is not a Kernel-level RCE "
                    "(check CVE database if available)"
                )
        
        # Base image check (already done in schema validation)
        # Port check (would need Dockerfile analysis in real implementation)
        if "environment" in self.mission:
            env = self.mission["environment"]
            if "base_image" in env:
                base_image = env["base_image"]
                if base_image not in ALLOWED_BASE_IMAGES:
                    self.warnings.append(
                        f"base_image '{base_image}' may not comply with security standards. "
                        f"Recommended: {ALLOWED_BASE_IMAGES}"
                    )
    
    def _validate_consistency(self):
        """Additional consistency checks."""
        # Check if mission_id and image name are consistent
        if "mission_id" in self.mission and "environment" in self.mission:
            mission_id = self.mission["mission_id"]
            env = self.mission["environment"]
            if "image" in env:
                image = env["image"]
                # Extract mission code from mission_id (e.g., "SOL-MSN-XXX" -> "xxx")
                mission_code = mission_id.split("-")[-1].lower() if "-" in mission_id else ""
                if mission_code and mission_code not in image.lower():
                    self.warnings.append(
                        f"mission_id '{mission_id}' and image '{image}' may not be consistent"
                    )


def validate_mission_file(file_path: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validate a mission JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    path = Path(file_path)
    
    if not path.exists():
        raise ValidationError(f"File not found: {file_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            mission_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON: {e}")
    except Exception as e:
        raise ValidationError(f"Error reading file: {e}")
    
    validator = MissionValidator(mission_data)
    return validator.validate_all()


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validator.py <mission_json_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
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
            sys.exit(1)
        else:
            print("✓ Validation PASSED", file=sys.stdout)
            if warnings:
                print(f"  ({len(warnings)} warning(s))", file=sys.stdout)
            sys.exit(0)
    
    except ValidationError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

