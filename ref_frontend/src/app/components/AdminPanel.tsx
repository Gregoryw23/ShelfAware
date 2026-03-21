import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { BookOpen, Sparkles, CheckCircle, AlertCircle } from 'lucide-react';
import { mockReviews } from '../data/mockData';
import { apiService, Book } from '../services/api';
import { toast } from 'sonner';

export function AdminPanel() {
  const [books, setBooks] = useState<Book[]>([]);
  const [isLoadingBooks, setIsLoadingBooks] = useState(true);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState<string | null>(null);

  const loadBooks = async () => {
    try {
      setIsLoadingBooks(true);
      const dbBooks = await apiService.getBooks();
      setBooks(dbBooks);
    } catch (error) {
      console.error('Error loading books:', error);
      toast.error('Failed to load books from database');
    } finally {
      setIsLoadingBooks(false);
    }
  };

  useEffect(() => {
    loadBooks();
  }, []);

  const handleGenerateSummary = async (bookId: string) => {
    setIsGeneratingSummary(bookId);
    try {
      await fetch('http://localhost:8000/admin/sync-synopses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      await loadBooks();
      toast.success('Synopsis sync triggered and books reloaded');
    } catch (error) {
      console.error('Error syncing summaries:', error);
      toast.error('Failed to trigger synopsis sync');
    } finally {
      setIsGeneratingSummary(null);
    }
  };

  const pendingReviews = mockReviews.filter((r) => !r.moderated);
  const moderatedReviews = mockReviews.filter((r) => r.moderated);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
          <p className="text-gray-600">Manage database book data and moderate reviews</p>
        </div>
        <Button variant="outline" onClick={loadBooks} disabled={isLoadingBooks}>
          Refresh Books
        </Button>
      </div>

      <Tabs defaultValue="books" className="w-full">
        <TabsList>
          <TabsTrigger value="books">
            <BookOpen className="size-4 mr-2" />
            Book Management ({books.length})
          </TabsTrigger>
          <TabsTrigger value="reviews">
            <AlertCircle className="size-4 mr-2" />
            Review Moderation ({pendingReviews.length} pending)
          </TabsTrigger>
        </TabsList>

        <TabsContent value="books" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Book Catalog</CardTitle>
            </CardHeader>
            <CardContent>
              <Table className="w-full table-fixed">
                <TableHeader>
                  <TableRow>
                    <TableHead>Cover</TableHead>
                    <TableHead className="w-[280px]">Title</TableHead>
                    <TableHead className="w-[360px]">Community Review</TableHead>
                    <TableHead>Pages</TableHead>
                    <TableHead>Published</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoadingBooks ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                        Loading books from app.db...
                      </TableCell>
                    </TableRow>
                  ) : books.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                        No books found in database
                      </TableCell>
                    </TableRow>
                  ) : (
                    books.map((book) => (
                      <TableRow key={book.book_id}>
                        <TableCell>
                          <img
                            src={book.cover_image_url || 'https://via.placeholder.com/80x120?text=No+Cover'}
                            alt={book.title}
                            className="w-12 h-16 object-cover rounded"
                          />
                        </TableCell>
                        <TableCell className="w-[280px] max-w-[280px]">
                          <span
                            className="font-medium whitespace-normal break-words leading-5"
                            style={{
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical',
                              overflow: 'hidden',
                            }}
                            title={book.title}
                          >
                            {book.title}
                          </span>
                        </TableCell>
                        <TableCell className="w-[360px] max-w-[360px]">
                          <span
                            className="text-sm text-gray-700 whitespace-normal break-words leading-5"
                            style={{
                              display: '-webkit-box',
                              WebkitLineClamp: 3,
                              WebkitBoxOrient: 'vertical',
                              overflow: 'hidden',
                            }}
                            title={book.CommunitySynopsis || 'No community review available'}
                          >
                            {book.CommunitySynopsis || '-'}
                          </span>
                        </TableCell>
                        <TableCell>{book.page_count ?? '-'}</TableCell>
                        <TableCell>
                          {book.published_date ? new Date(book.published_date).getFullYear() : '-'}
                        </TableCell>
                        <TableCell>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleGenerateSummary(book.book_id)}
                            disabled={isGeneratingSummary === book.book_id}
                          >
                            {isGeneratingSummary === book.book_id ? (
                              <>Syncing...</>
                            ) : (
                              <>
                                <Sparkles className="size-3 mr-1" />
                                Sync Synopsis
                              </>
                            )}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reviews" className="mt-6">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <AlertCircle className="size-5 mr-2 text-orange-500" />
                  Pending Reviews ({pendingReviews.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {pendingReviews.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">No pending reviews</p>
                ) : (
                  <div className="space-y-4">
                    {pendingReviews.map((review) => {
                      const book = books.find((b) => b.book_id === review.bookId);
                      return (
                        <div key={review.id} className="border rounded-lg p-4">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h4 className="font-semibold">{book?.title}</h4>
                              <p className="text-sm text-gray-600">
                                Rating: {review.rating}/5 • {new Date(review.date).toLocaleDateString()}
                              </p>
                            </div>
                            <div className="flex gap-2">
                              <Button size="sm" onClick={() => toast.success('Review approved')}>
                                <CheckCircle className="size-4 mr-1" />
                                Approve
                              </Button>
                              <Button size="sm" variant="outline" onClick={() => toast.success('Review rejected')}>
                                Reject
                              </Button>
                            </div>
                          </div>
                          <div className="flex flex-wrap gap-2 mb-2">
                            {review.emotion.map((emotion) => (
                              <Badge key={emotion} variant="outline" className="text-xs">
                                {emotion}
                              </Badge>
                            ))}
                          </div>
                          <p className="text-sm text-gray-700">{review.content}</p>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CheckCircle className="size-5 mr-2 text-green-500" />
                  Approved Reviews ({moderatedReviews.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {moderatedReviews.slice(0, 5).map((review) => {
                    const book = books.find((b) => b.book_id === review.bookId);
                    return (
                      <div key={review.id} className="border rounded-lg p-4 bg-green-50">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="font-semibold">{book?.title}</h4>
                            <p className="text-sm text-gray-600">
                              Rating: {review.rating}/5 • {review.helpful} helpful votes
                            </p>
                          </div>
                          <Badge variant="secondary" className="bg-green-200">
                            Approved
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-700">{review.content}</p>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}