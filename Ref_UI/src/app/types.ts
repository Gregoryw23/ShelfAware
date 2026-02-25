// Type definitions for Shelf Aware

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  reputation: number;
  role: 'user' | 'admin';
}

export interface Book {
  id: string;
  title: string;
  author: string;
  cover: string;
  genre: string[];
  abstract: string;
  averageRating: number;
  totalReviews: number;
  price?: number;
  condition?: string;
}

export interface ReadingProgress {
  bookId: string;
  progress: number; // 0-100
  startDate: string;
  lastRead: string;
  status: 'reading' | 'completed' | 'want-to-read';
}

export interface Review {
  id: string;
  userId: string;
  bookId: string;
  rating: number;
  emotion: string[];
  content: string;
  date: string;
  helpful: number;
  moderated: boolean;
}

export interface MoodEntry {
  date: string;
  mood: string;
  emotions: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}
