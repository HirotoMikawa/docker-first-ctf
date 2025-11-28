"""
Project Sol: Flag Placement Validator

Validates that flag is placed in the correct location based on problem type.
"""

import re
from typing import Tuple, List


def validate_flag_placement(dockerfile_content: str, problem_type: str, expected_flag: str) -> Tuple[bool, List[str]]:
    """
    Validate that flag is placed in the correct location based on problem type.
    
    Args:
        dockerfile_content: Dockerfile content as string
        problem_type: Problem type (e.g., "RCE", "SQLi", "SSRF")
        expected_flag: Expected flag value (e.g., "SolCTF{...}")
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    problem_type = problem_type.upper()
    
    # Check if expected_flag is in dockerfile
    if expected_flag not in dockerfile_content:
        errors.append(f"Expected flag '{expected_flag}' not found in Dockerfile")
    
    # Rule #1: RCE / LFI / PrivEsc / Misconfig → /home/ctfuser/flag.txt
    if problem_type in ["RCE", "LFI", "PRIVESC", "MISCONFIG"]:
        # Check for correct path
        if "/home/ctfuser/flag.txt" not in dockerfile_content:
            errors.append(f"Problem type '{problem_type}' requires flag at /home/ctfuser/flag.txt, but not found in Dockerfile")
        
        # Check for incorrect path (should NOT use /flag.txt)
        if re.search(r'RUN\s+echo\s+.*>\s+/flag\.txt', dockerfile_content):
            errors.append(f"Problem type '{problem_type}' should use /home/ctfuser/flag.txt, but found /flag.txt in Dockerfile")
        
        # Check for correct format
        if not re.search(r'RUN\s+echo\s+.*>\s+/home/ctfuser/flag\.txt', dockerfile_content):
            errors.append(f"Problem type '{problem_type}' requires: RUN echo ... > /home/ctfuser/flag.txt")
    
    # Rule #2: Web problems (SQLi / XSS / SSRF / XXE / IDOR) → /flag.txt + ENV
    elif problem_type in ["SQLI", "XSS", "SSRF", "XXE", "IDOR"]:
        # Check for /flag.txt
        if "/flag.txt" not in dockerfile_content:
            errors.append(f"Problem type '{problem_type}' requires flag at /flag.txt, but not found in Dockerfile")
        
        # Check for ENV FLAG
        if not re.search(r'ENV\s+FLAG\s*=', dockerfile_content, re.IGNORECASE):
            errors.append(f"Problem type '{problem_type}' requires ENV FLAG variable, but not found in Dockerfile")
        
        # Check for incorrect path (should NOT use /home/ctfuser/flag.txt)
        if re.search(r'RUN\s+echo\s+.*>\s+/home/ctfuser/flag\.txt', dockerfile_content):
            errors.append(f"Problem type '{problem_type}' should use /flag.txt, but found /home/ctfuser/flag.txt in Dockerfile")
    
    # Rule #3: LogicError / Crypto → flexible (code or file)
    elif problem_type in ["LOGICERROR", "CRYPTO"]:
        # These are flexible, so we just check that flag exists somewhere
        if expected_flag not in dockerfile_content:
            errors.append(f"Problem type '{problem_type}' requires flag somewhere (code or file), but not found")
    
    return len(errors) == 0, errors

