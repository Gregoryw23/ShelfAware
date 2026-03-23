import React, { useEffect, useState } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { BookOpen, Clock, Loader2, Plus, Search } from 'lucide-react';
import { apiService, Book } from '../services/api';
import { useNavigate } from 'react-router';
import { toast } from 'sonner';

interface InspirationProps {
  accessToken: string | null;
}

export function Inspiration({ accessToken }: InspirationProps) {
  const navigate = useNavigate();
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchBooks = async () => {
      try {
        setLoading(true);
        const fetchedBooks = await apiService.getBooks();
        setBooks(fetchedBooks);
        setError(null);
      } catch (err) {
        setError('Failed to load books. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchBooks();
  }, []);

  const booksWithPresentationFields = books.map((book) => ({
    ...book,
    id: book.book_id,
    cover: book.cover_image_url || 'https://via.placeholder.com/400x600?text=No+Cover',
  }));

  const filteredBooks = booksWithPresentationFields.filter((book) =>
    book.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAddToBookshelf = async (bookId: string) => {
    if (!accessToken) {
      toast.error('Please sign in to add books to your shelf');
      return;
    }

    try {
      console.log(`Adding book ${bookId} to shelf...`);
      await apiService.addToBookshelf(accessToken, bookId);
      toast.success('Added to your bookshelf');
    } catch (err) {
      console.error('Add to bookshelf error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to add to bookshelf';
      toast.error(errorMessage);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading books...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>Try Again</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">Inspiration</h1>
        <p className="text-gray-600">Explore the full book database and find your next read</p>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="relative max-w-md mx-auto">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 size-4" />
            <Input
              placeholder="Search books..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {filteredBooks.map((book) => (
          <Card
            key={book.id}
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => navigate(`/book/${book.id}`)}
          >
            <div className="aspect-[2/3] relative overflow-hidden rounded-t-lg">
              <img src={book.cover} alt={book.title} className="w-full h-full object-cover" />
              <div className="absolute bottom-0 left-0 right-0 bg-black/55 p-2 text-white text-xs flex justify-between">
                {book.page_count ? <span>{book.page_count} pages</span> : <span />}
                {book.published_date ? <span>{new Date(book.published_date).getFullYear()}</span> : <Clock className="size-3" />}
              </div>
            </div>
            <CardContent className="p-4">
              <h3 className="font-semibold line-clamp-2">{book.title}</h3>
              {book.subtitle && <p className="text-sm text-gray-600 mt-1 line-clamp-1">{book.subtitle}</p>}
              {book.abstract && <p className="text-xs text-gray-500 line-clamp-2 mt-2">{book.abstract}</p>}
              <Button
                type="button"
                size="sm"
                className="mt-3 w-full"
                variant="outline"
                onClick={(e) => {
                  e.stopPropagation();
                  handleAddToBookshelf(book.id);
                }}
              >
                <Plus className="size-4 mr-2" />
                Add to Bookshelf
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredBooks.length === 0 && !loading && (
        <div className="text-center py-12">
          <BookOpen className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No books found</h3>
          <p className="text-gray-500">Try adjusting your search terms.</p>
        </div>
      )}
    </div>
  );
}
