export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superadmin: boolean;
  created_at: string;
}

export interface Meeting {
  id: number;
  user_id: number;
  name: string;
  original_filename: string;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ChatMessage {
  content: string;
  is_user: boolean;
}

export interface ApiError {
  detail: string;
}
