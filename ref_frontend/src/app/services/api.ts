// API service for connecting to the ShelfAware backend
const API_BASE_URL = 'http://localhost:8000';

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
  book_id: string;
  rating: number;
  comment?: string;
  mood?: string;
  created_at: string;
}

export interface ReviewCreate {
  rating: number;
  comment?: string;
  mood?: string;
}

export interface ChatRequest {
  message: string;
  user_id?: string;
}

export interface ChatBookRecommendation {
  book_id: string;
  title: string;
  subtitle?: string | null;
  abstract?: string | null;
  cover_image_url?: string | null;
  genres?: string[];
}

export interface ChatResponse {
  response: string;
  mood: string;
  books: ChatBookRecommendation[];
  follow_up_questions: string[];
}

class ApiService {
  private async request(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${API_BASE_URL}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Books API
  async getBooks(): Promise<Book[]> {
    return this.request('/books/');
  }

  async getBook(bookId: string): Promise<Book> {
    return this.request(`/books/${bookId}`);
  }

  // Reviews API
  async getReviewsForBook(bookId: string): Promise<Review[]> {
    return this.request(`/reviews/book/${bookId}`);
  }

  async addReview(bookId: string, review: ReviewCreate): Promise<Review> {
    return this.request(`/reviews/books/${bookId}`, {
      method: 'POST',
      body: JSON.stringify(review),
    });
  }

  // Chatbot API
  async chat(request: ChatRequest): Promise<ChatResponse> {
    return this.request('/api/chatbot/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }
}

export const apiService = new ApiService();