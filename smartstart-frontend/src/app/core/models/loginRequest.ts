export interface LoginRequest {
  email: string;
  password: string;
  role?: 'STARTUPER' | 'INVESTOR';
}
