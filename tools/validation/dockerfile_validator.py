"""
Project Sol: Dockerfile Validator

Validates Dockerfile to ensure user creation is correct.
"""

import re
from typing import List, Tuple


def validate_dockerfile_user_creation(dockerfile_content: str) -> Tuple[bool, List[str]]:
    """
    Validate that Dockerfile correctly creates ctfuser before using USER ctfuser.
    
    Args:
        dockerfile_content: Dockerfile content as string
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    lines = dockerfile_content.split('\n')
    
    # Check if USER ctfuser is present
    user_ctfuser_line = None
    user_ctfuser_index = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('USER') and 'ctfuser' in stripped:
            user_ctfuser_line = stripped
            user_ctfuser_index = i
            break
    
    if user_ctfuser_line is None:
        # No USER ctfuser found, that's okay (might use root or different user)
        return True, []
    
    # Check if useradd or adduser is present before USER ctfuser
    user_creation_found = False
    user_creation_line = None
    
    for i in range(user_ctfuser_index):
        line = lines[i].strip()
        # Check for useradd (Debian/Ubuntu)
        if re.search(r'useradd\s+.*ctfuser', line, re.IGNORECASE):
            user_creation_found = True
            user_creation_line = line
            # Check for problematic -s /bin/bash option
            if re.search(r'-s\s+/bin/bash', line):
                errors.append(f"Line {i+1}: useradd with -s /bin/bash may fail (bash not installed in python:3.11-slim). Use 'RUN useradd -m -u 1000 ctfuser' instead.")
            break
        # Check for adduser (Alpine)
        elif re.search(r'adduser\s+.*ctfuser', line, re.IGNORECASE):
            user_creation_found = True
            user_creation_line = line
            break
    
    if not user_creation_found:
        errors.append(f"Line {user_ctfuser_index+1}: USER ctfuser found but no useradd/adduser command found before it. User must be created before switching to it.")
    
    return len(errors) == 0, errors

