// src/app/core/interceptors/auth.interceptor.ts

import { HttpInterceptorFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const TOKEN_KEYS = ['access_token', 'token', 'authToken', 'jwt', 'auth_token'];
  
  let token: string | null = null;
  for (const key of TOKEN_KEYS) {
    token = localStorage.getItem(key) ?? sessionStorage.getItem(key);
    if (token) break;
  }

  if (!token) return next(req);

  return next(req.clone({
    setHeaders: { Authorization: `Bearer ${token}` }
  }));
};