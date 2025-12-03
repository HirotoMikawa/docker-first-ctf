export interface Challenge {
  challenge_id: string;
  title: string;
  description?: string;
  difficulty?: number; // DB column is now integer (1-5)
  category?: string;
  points?: number;
  writeup?: string; // Educational writeup in Markdown format
  tags?: string[]; // Tags array (e.g., ["Web", "SQL", "Beginner"])
  metadata?: {
    tags?: string[]; // Alternative location for tags
    category?: string; // Category key (e.g., "WEB_SQLI")
    [key: string]: any; // Allow other metadata fields
  };
}

export interface MissionData {
  status: string;
  container_id: string;
  port: number;
  url: string;
  message: string;
  challenge_name?: string;
  challenge_id?: string; // Flag提出時に必要
}

export interface SubmitResult {
  correct: boolean;
  message: string;
}

