// Type definitions for Shelf Aware - matching backend API

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  reputation: number;
  role: 'user' | 'admin';
}

export interface Book {
  book_id: string;
  title: string;
  subtitle?: string;
  cover_image_url?: string;
  abstract?: string;
  CommunitySynopsis?: string;
  page_count?: number;
  published_date?: string;
  created_at: string;
}

export interface Review {
  review_id: string;
  book_id: string | number;
  user_id: string;
  rating: number;
  comment?: string;
  body?: string;
  mood?: string;
  created_at: string;
  updated_at: string;
}

export interface ReadingProgress {
  bookId: string;
  progress: number; // 0-100
  startDate: string;
  lastRead: string;
  status: 'reading' | 'completed' | 'want-to-read';
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
