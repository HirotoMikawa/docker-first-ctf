"""
Project Sol: Marketing Content Generator (Ver 10.2)

Generates SNS content in "Game Master" challenge format.
Uses Hook-Body-CTA framework to maximize engagement.

Uses OpenAI API (gpt-4o-mini) for AI-powered generation.
"""

import json
import re
import os
from typing import Dict, Any, Optional
from datetime import datetime
import sys

# Load environment variables
from dotenv import load_dotenv

# OpenAI API
try:
    from openai import OpenAI
except ImportError:
    print("Error: openai library not installed. Run: pip install -r tools/requirements.txt", file=sys.stderr)
    sys.exit(1)

# Load .env file
load_dotenv()


# Forbidden Words (CONTENT_PLAN.md SSOT)
FORBIDDEN_WORDS = [
    "Great", "Good luck", "Happy", "Sorry", "Please", 
    "I think", "Feel", "Hope"
]
FORBIDDEN_PUNCTUATION = "!"


class ContentGenerator:
    """Generates marketing content in "Game Master" challenge format using OpenAI API."""
    
    def __init__(self, mission_data: Dict[str, Any], base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize generator.
        
        Args:
            mission_data: Mission JSON data
            base_url: Base URL for mission links (optional)
            api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
        """
        self.mission = mission_data
        self.base_url = base_url or "https://project-sol.example.com"
        
        # Initialize OpenAI client
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. "
                "Please set it as an environment variable or pass it as api_key parameter."
            )
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    def _contains_forbidden_content(self, text: str) -> bool:
        """
        Check if text contains forbidden words or punctuation.
        
        Args:
            text: Text to check
            
        Returns:
            True if forbidden content is found, False otherwise
        """
        text_lower = text.lower()
        
        # Check forbidden words
        for word in FORBIDDEN_WORDS:
            if word.lower() in text_lower:
                return True
        
        # Check forbidden punctuation
        if FORBIDDEN_PUNCTUATION in text:
            return True
        
        return False
    
    def _generate_intel_post_with_ai(self, max_retries: int = 3) -> str:
        """
        Generate challenging SNS post using OpenAI API.
        Uses "Game Master" tone with Hook-Body-CTA framework.
        
        Args:
            max_retries: Maximum retry attempts if forbidden content is detected
            
        Returns:
            Generated SNS post text
        """
        # Extract mission data
        mission_type = self.mission.get("type", "Unknown")
        difficulty = self.mission.get("difficulty", 0)
        vulnerability = self.mission.get("vulnerability", {})
        cve_id = vulnerability.get("cve_id", "CVE-XXXX-XXXX")
        mission_id = self.mission.get("mission_id", "SOL-MSN-XXX")
        
        # Build URL
        mission_slug = mission_id.lower().replace("-", "_")
        url = f"{self.base_url}/mission/{mission_slug}"
        
        # System Prompt
        system_prompt = """You are the "Game Master" of Project Sol. Your goal is to provoke hackers and engineers to prove their skills. You are energetic, challenging, and professional.

**Your Role:**
- You are an elite hacker recruiter and challenge creator
- Your mission is to make users want to prove their skills
- You create posts that spark competition and urgency

**Tone Requirements:**
- **Challenging**: "Can you crack this?", "Think you know {type}?"
- **Urgent**: "System is live. Time is ticking.", "Be the first to pwn this system."
- **Exclusive**: "Only for the top 1%.", "Current solve rate: 0%."
- **Energetic**: Be aggressive in a fun way. NEVER sound bored or passive.

**Forbidden Words (ABSOLUTELY PROHIBITED):**
- Words: "Great", "Good luck", "Happy", "Sorry", "Please", "I think", "Feel", "Hope"
- Punctuation: ! (Exclamation mark)

**Output Templates (Choose ONE randomly):**

1. **The Skill Check:**
   "🔥 [Vulnerability Type] Challenge
   Difficulty: {diff}/5
   
   Think you know {type}? This mission will test your limits. The target '{target_name}' is vulnerable, but only the best can find the entry point.
   
   Prove your skills: {url}
   #ProjectSol #CTF #CyberSecurity"

2. **The "Impossible" Challenge:**
   "⚠️ WARNING: High Difficulty
   
   Mission ID: {mission_id}
   Target: {target_name}
   
   Current solve rate: 0%. Be the first to pwn this system. It won't be easy.
   
   Deploy now: {url}
   #ProjectSol #Hacking"

3. **The Story Hook:**
   "🕵️ MISSION ALERT
   
   Intel reports a massive security oversight in {target_name}. We need an agent to exploit this {type} vulnerability before they patch it.
   
   Are you up for the task?
   👉 {url}
   #ProjectSol #InfoSec"

**Constraints:**
- Use relevant emojis (🔥, 💀, 💻, 🛡️, ⚠️, 🕵️, 👉) effectively
- Keep it under 200 characters (excluding URL/Tags)
- NEVER sound bored or passive. Be aggressive in a fun way
- Always include #ProjectSol hashtag
- NEVER use forbidden words or exclamation marks"""
        
        # Extract target name from narrative or use mission_id
        narrative = self.mission.get("narrative", {})
        story_hook = narrative.get("story_hook", "")
        # Try to extract target name from story_hook (first few words or mission_id)
        target_name = mission_id  # Default to mission_id
        if story_hook:
            # Extract first meaningful phrase (up to 3 words)
            words = story_hook.split()[:3]
            if words:
                target_name = " ".join(words).rstrip(".,!?")
        
        # User Prompt
        user_prompt = f"""Create a challenging SNS post (Twitter/X format) that makes hackers want to prove their skills.

**Mission Information:**
- Type: {mission_type}
- Difficulty: {difficulty}/5
- CVE: {cve_id}
- Mission ID: {mission_id}
- Target Name: {target_name}
- URL: {url}

**Instructions:**
- Choose ONE of the three templates (The Skill Check, The "Impossible" Challenge, or The Story Hook)
- Fill in the placeholders with the mission information above
- Make it challenging, urgent, and exclusive
- Use emojis effectively (🔥, 💀, 💻, 🛡️, ⚠️, 🕵️, 👉)
- Keep it under 200 characters (excluding URL and hashtags)
- NEVER use forbidden words or exclamation marks
- Always include #ProjectSol hashtag

**Output:**
Generate the post in the chosen template format. Be energetic and make users want to take on the challenge."""
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                
                generated_text = response.choices[0].message.content.strip()
                
                # Validate: Check for forbidden content
                if self._contains_forbidden_content(generated_text):
                    if attempt < max_retries - 1:
                        continue  # Retry
                    else:
                        # Last attempt, remove forbidden content manually
                        generated_text = self._sanitize_forbidden_content(generated_text)
                
                # Ensure hashtag is present
                if "#ProjectSol" not in generated_text:
                    generated_text += "\n#ProjectSol"
                
                return generated_text
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"OpenAI API call failed after {max_retries} attempts: {e}")
                continue
        
        # Fallback (should not reach here)
        return self._generate_fallback_teaser()
    
    def _sanitize_forbidden_content(self, text: str) -> str:
        """
        Remove forbidden words and punctuation from text.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        # Remove forbidden words
        for word in FORBIDDEN_WORDS:
            text = re.sub(
                re.escape(word),
                "",
                text,
                flags=re.IGNORECASE
            )
        
        # Remove forbidden punctuation
        text = text.replace(FORBIDDEN_PUNCTUATION, ".")
        
        return text
    
    def _generate_fallback_teaser(self) -> str:
        """
        Generate fallback teaser if AI generation fails.
        Uses "The Skill Check" template style.
        
        Returns:
            Fallback teaser text
        """
        mission_id = self.mission.get("mission_id", "SOL-MSN-XXX")
        mission_type = self.mission.get("type", "Unknown")
        difficulty = self.mission.get("difficulty", 0)
        vulnerability = self.mission.get("vulnerability", {})
        cve_id = vulnerability.get("cve_id", "CVE-XXXX-XXXX")
        
        mission_slug = mission_id.lower().replace("-", "_")
        url = f"{self.base_url}/mission/{mission_slug}"
        
        # Use "The Skill Check" template as fallback
        return f"""🔥 {mission_type} Challenge
Difficulty: {difficulty}/5

Think you know {mission_type}? This mission will test your limits. The target '{mission_id}' is vulnerable, but only the best can find the entry point.

Prove your skills: {url}
#ProjectSol #CTF #CyberSecurity"""
    
    def generate_sns_teaser(self, max_length: int = 280, use_ai: bool = True) -> str:
        """
        Generate SNS teaser in "Game Master" challenge format using OpenAI API.
        
        Uses Hook-Body-CTA framework with three templates:
        - The Skill Check: Challenges users to prove their skills
        - The "Impossible" Challenge: Creates urgency with 0% solve rate
        - The Story Hook: Uses narrative to engage users
        
        Args:
            max_length: Maximum character length (default: 280 for Twitter)
            use_ai: Use OpenAI API for generation (default: True)
            
        Returns:
            SNS teaser text
        """
        if use_ai:
            try:
                return self._generate_intel_post_with_ai()
            except Exception as e:
                print(f"Warning: AI generation failed, using fallback: {e}", file=sys.stderr)
                return self._generate_fallback_teaser()
        else:
            # Fallback to original method
            return self._generate_fallback_teaser()
    
    def generate_mission_briefing(self) -> str:
        """
        Generate Mission Briefing in Combat Mode format.
        
        Format (CONTENT_PLAN.md Section 4.A):
        === MISSION BRIEFING ===
        **Mission ID:** {SOL-MSN-XXX}
        **Objective:** {Flag Location}
        **Threat Level:** {1-5}
        
        **Intel:**
        {Target info - Combat Mode - Max 3 lines}
        
        [COMMAND] Proceed: Y / Abort: N
        
        Returns:
            Mission briefing text
        """
        mission_id = self.mission.get("mission_id", "SOL-MSN-XXX")
        difficulty = self.mission.get("difficulty", 0)
        narrative = self.mission.get("narrative", {})
        story_hook = narrative.get("story_hook", "Target system detected.")
        
        # Extract objective from story_hook or use default
        objective = self._extract_objective(story_hook)
        
        lines = [
            "=== MISSION BRIEFING ===",
            f"**Mission ID:** {mission_id}",
            f"**Objective:** {objective}",
            f"**Threat Level:** {difficulty}",
            "",
            "**Intel:**",
            story_hook,
            "",
            "[COMMAND] Proceed: Y / Abort: N"
        ]
        
        return "\n".join(lines)
    
    def _extract_commentary(self, story_hook: str) -> str:
        """
        Extract commentary from story_hook.
        Sanitize to avoid forbidden words and punctuation.
        
        Args:
            story_hook: Original story hook text
            
        Returns:
            Sanitized commentary
        """
        # Take first sentence
        sentences = re.split(r'[.!?]+', story_hook)
        if sentences:
            commentary = sentences[0].strip()
        else:
            commentary = story_hook.strip()
        
        # Remove forbidden words
        commentary_lower = commentary.lower()
        for word in FORBIDDEN_WORDS:
            word_lower = word.lower()
            if word_lower in commentary_lower:
                # Replace with neutral alternative
                commentary = re.sub(
                    re.escape(word),
                    "[REDACTED]",
                    commentary,
                    flags=re.IGNORECASE
                )
        
        # Remove forbidden punctuation
        commentary = commentary.replace(FORBIDDEN_PUNCTUATION, ".")
        
        # Ensure it's not empty
        if not commentary or len(commentary) < 10:
            commentary = "Target system requires immediate investigation."
        
        return commentary
    
    def _extract_objective(self, story_hook: str) -> str:
        """
        Extract objective from story_hook.
        
        Args:
            story_hook: Original story hook text
            
        Returns:
            Objective description
        """
        # Try to extract key information
        # Look for common patterns like "Flag:", "Find:", "Retrieve:"
        flag_pattern = re.search(r'(?:Flag|flag|FLAG)[:\s]+([A-Za-z0-9_\-{}]+)', story_hook)
        if flag_pattern:
            return f"Retrieve flag: {flag_pattern.group(1)}"
        
        # Look for IP addresses
        ip_pattern = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', story_hook)
        if ip_pattern:
            return f"Investigate target at {ip_pattern.group(0)}"
        
        # Default
        return "Extract classified information from target system"


def generate_from_file(file_path: str, output_format: str = "sns", base_url: Optional[str] = None, api_key: Optional[str] = None, use_ai: bool = True) -> str:
    """
    Generate content from mission JSON file.
    
    Args:
        file_path: Path to mission JSON file
        output_format: "sns" or "briefing"
        base_url: Base URL for mission links (optional)
        api_key: OpenAI API key (optional)
        use_ai: Use OpenAI API for SNS generation (default: True)
        
    Returns:
        Generated content text
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            mission_data = json.load(f)
    except FileNotFoundError:
        raise ValueError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    
    generator = ContentGenerator(mission_data, base_url, api_key)
    
    if output_format == "sns":
        return generator.generate_sns_teaser(use_ai=use_ai)
    elif output_format == "briefing":
        return generator.generate_mission_briefing()
    else:
        raise ValueError(f"Unknown output format: {output_format}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python generator.py <mission_json_file> <sns|briefing> [base_url]", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    output_format = sys.argv[2]
    base_url = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        content = generate_from_file(file_path, output_format, base_url)
        print(content)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

