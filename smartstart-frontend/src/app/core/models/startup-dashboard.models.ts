// src/app/core/models/startup-dashboard.models.ts

export interface AIAssistantRequest {
  message: string;
  action?: 'summary' | 'career_advice' | 'custom';
}

export interface AIAssistantResponse {
  result: string;
  action?: string;
}

export interface ChatMessage {
  role: 'user' | 'ai';
  text: string;
  timestamp: Date;
}
