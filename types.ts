
export interface ChatMessage {
  role: 'user' | 'bot' | 'status';
  content: string;
}
