import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { BookOpen, Sparkles, CheckCircle, AlertCircle } from 'lucide-react';
import { apiService, Book, SynopsisModerationItem } from '../services/api';
import { toast } from 'sonner';

export function AdminPanel() {
  const [books, setBooks] = useState<Book[]>([]);
  const [isLoadingBooks, setIsLoadingBooks] = useState(true);
  const [isSyncingSynopsis, setIsSyncingSynopsis] = useState(false);
  const [isLoadingModeration, setIsLoadingModeration] = useState(false);
  const [moderationItems, setModerationItems] = useState<SynopsisModerationItem[]>([]);
  const [processingModerationId, setProcessingModerationId] = useState<string | null>(null);

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
    loadModerationItems();
  }, []);

  const loadModerationItems = async () => {
    try {
      setIsLoadingModeration(true);
      const response = await apiService.getSynopsisModeration('pending');
      setModerationItems(response.items || []);
    } catch (error) {
      console.error('Error loading moderation items:', error);
      toast.error('Failed to load synopsis moderation queue');
    } finally {
      setIsLoadingModeration(false);
    }
  };

  const handleSyncSynopsis = async () => {
    setIsSyncingSynopsis(true);
    try {
      const result = await apiService.triggerSynopsisSync();
      await Promise.all([loadBooks(), loadModerationItems()]);
      toast.success(
        `Sync complete. Proposed: ${result.proposed}, Refreshed: ${result.refreshed}, Skipped: ${result.skipped}`
      );
    } catch (error) {
      console.error('Error syncing summaries:', error);
      toast.error('Failed to trigger synopsis sync');
    } finally {
      setIsSyncingSynopsis(false);
    }
  };

  const handleModerationAction = async (moderationId: string, action: 'accept' | 'reject') => {
    setProcessingModerationId(moderationId);
    try {
      if (action === 'accept') {
        await apiService.acceptSynopsisModeration(moderationId);
        toast.success('Synopsis accepted and community review updated');
      } else {
        await apiService.rejectSynopsisModeration(moderationId);
        toast.success('Synopsis proposal rejected');
      }
      await Promise.all([loadBooks(), loadModerationItems()]);
    } catch (error) {
      console.error('Error handling moderation action:', error);
      toast.error('Failed to process moderation action');
    } finally {
      setProcessingModerationId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
          <p className="text-gray-600">Manage book data and moderate community synopsis updates</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadBooks} disabled={isLoadingBooks}>
            Refresh Books
          </Button>
          <Button onClick={handleSyncSynopsis} disabled={isSyncingSynopsis}>
            <Sparkles className="size-4 mr-2" />
            {isSyncingSynopsis ? 'Syncing...' : 'Sync Synopses'}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="books" className="w-full">
        <TabsList>
          <TabsTrigger value="books">
            <BookOpen className="size-4 mr-2" />
            Book Management ({books.length})
          </TabsTrigger>
          <TabsTrigger value="reviews">
            <AlertCircle className="size-4 mr-2" />
            Synopsis Moderation ({moderationItems.length} pending)
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
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoadingBooks ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                        Loading books from app.db...
                      </TableCell>
                    </TableRow>
                  ) : books.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8 text-gray-500">
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
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reviews" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <AlertCircle className="size-5 mr-2 text-orange-500" />
                Pending Synopsis Changes ({moderationItems.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoadingModeration ? (
                <p className="text-center text-gray-500 py-8">Loading moderation queue...</p>
              ) : moderationItems.length === 0 ? (
                <p className="text-center text-gray-500 py-8">No pending synopsis changes</p>
              ) : (
                <div className="space-y-4">
                  {moderationItems.map((item) => (
                    <div key={item.moderation_id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold">{item.book_title}</h4>
                          <p className="text-sm text-gray-600">
                            Source synopses: {item.user_synopsis_count}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => handleModerationAction(item.moderation_id, 'accept')}
                            disabled={processingModerationId === item.moderation_id}
                          >
                            <CheckCircle className="size-4 mr-1" />
                            Accept
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleModerationAction(item.moderation_id, 'reject')}
                            disabled={processingModerationId === item.moderation_id}
                          >
                            Reject
                          </Button>
                        </div>
                      </div>

                      <div className="grid md:grid-cols-2 gap-3">
                        <div className="rounded-md border p-3 bg-gray-50">
                          <p className="text-xs uppercase tracking-wide text-gray-500 mb-2">Current Community Review</p>
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">{item.current_synopsis || '-'}</p>
                        </div>
                        <div className="rounded-md border p-3 bg-orange-50">
                          <p className="text-xs uppercase tracking-wide text-gray-500 mb-2">Proposed Update</p>
                          <p className="text-sm text-gray-800 whitespace-pre-wrap">{item.proposed_synopsis}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}