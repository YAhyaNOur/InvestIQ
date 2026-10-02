export interface User {
  user_id: number;
  username: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  roles: string[];
  avatar_url: string | null;
}