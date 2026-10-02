export interface RegisterRequest {
  username: string;
  email: string;
  full_name?: string;
  password: string;
  role?: string;  // "STARTUPER", "INVESTOR"
}