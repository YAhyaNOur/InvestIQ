export interface JwtPayload {
  sub: string;        // user_id (sous forme de string)
  type: string;       // "access"
  exp: number;
  iat: number;
  roles: string[];    // ex: ["STARTUPER"]
}