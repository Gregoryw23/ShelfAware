import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Switch } from './ui/switch';
import { BookOpen, Plus, Edit, Trash2, Sparkles, CheckCircle, AlertCircle } from 'lucide-react';
import { mockBooks, mockReviews } from '../data/mockData';
import { toast } from 'sonner';

export function AdminPanel() {
  const [books, setBooks] = useState(mockBooks);
  const [selectedBook, setSelectedBook] = useState<typeof mockBooks[0] | null>(null);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState<string | null>(null);

  // Form states for new/edit book
  const [formData, setFormData] = useState({
    title: '',
    author: '',
    genre: '',
    abstract: '',
    price: '',
    condition: 'New',
  });

  const handleGenerateSummary = (bookId: string) => {
    setIsGeneratingSummary(bookId);
    // Simulate LLM processing
    setTimeout(() => {
      const book = books.find((b) => b.id === bookId);
      if (book) {
        const reviews = mockReviews.filter((r) => r.bookId === bookId);
        const newAbstract = `AI-Generated Summary: This highly acclaimed book has received ${book.averageRating} stars from ${book.totalReviews} readers. Reviewers describe it as ${reviews[0]?.emotion.join(', ').toLowerCase() || 'engaging'}. ${book.abstract.substring(0, 150)}...`;
        
        setBooks(books.map((b) =>
          b.id === bookId ? { ...b, abstract: newAbstract } : b
        ));
        toast.success('Book abstract updated with LLM summary!');
      }
      setIsGeneratingSummary(null);
    }, 2000);
  };

  const handleAddBook = () => {
    const newBook = {
      id: Date.now().toString(),
      title: formData.title,
      author: formData.author,
      cover: 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400',
      genre: formData.genre.split(',').map((g) => g.trim()),
      abstract: formData.abstract,
      averageRating: 0,
      totalReviews: 0,
      price: parseFloat(formData.price) || 0,
      condition: formData.condition,
    };

    setBooks([...books, newBook]);
    setIsAddDialogOpen(false);
    setFormData({
      title: '',
      author: '',
      genre: '',
      abstract: '',
      price: '',
      condition: 'New',
    });
    toast.success('Book added successfully!');
  };

  const handleDeleteBook = (bookId: string) => {
    setBooks(books.filter((b) => b.id !== bookId));
    toast.success('Book deleted successfully!');
  };

  const pendingReviews = mockReviews.filter((r) => !r.moderated);
  const moderatedReviews = mockReviews.filter((r) => r.moderated);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
          <p className="text-gray-600">Manage book data and moderate reviews</p>
        </div>
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="size-4 mr-2" />
              Add New Book
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Add New Book</DialogTitle>
              <DialogDescription>
                Enter the details of the new book to add to the catalog
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="title">Title</Label>
                  <Input
                    id="title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="Book title"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="author">Author</Label>
                  <Input
                    id="author"
                    value={formData.author}
                    onChange={(e) => setFormData({ ...formData, author: e.target.value })}
                    placeholder="Author name"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="genre">Genres (comma-separated)</Label>
                <Input
                  id="genre"
                  value={formData.genre}
                  onChange={(e) => setFormData({ ...formData, genre: e.target.value })}
                  placeholder="Biography/Memoir, Psychology/Self-Help"
                />
                <p className="text-xs text-gray-500">
                  Available: Biography/Memoir, Military History, Science/Technology, Business/Economics, 
                  History, Nonfiction, Religion/Spirituality, Philosophy/Social Theory, Romance, Fantasy, 
                  Psychology/Self-Help, Science Fiction, Mystery/Thriller, Graphic Novel, Poetry
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="abstract">Abstract</Label>
                <Textarea
                  id="abstract"
                  value={formData.abstract}
                  onChange={(e) => setFormData({ ...formData, abstract: e.target.value })}
                  placeholder="Book description..."
                  rows={4}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="price">Price ($)</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    placeholder="19.99"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="condition">Condition</Label>
                  <Select
                    value={formData.condition}
                    onValueChange={(value) => setFormData({ ...formData, condition: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="New">New</SelectItem>
                      <SelectItem value="Like New">Like New</SelectItem>
                      <SelectItem value="Good">Good</SelectItem>
                      <SelectItem value="Fair">Fair</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button onClick={handleAddBook} className="w-full">
                Add Book
              </Button>
            </div>
          </DialogContent>
        </Dialog>
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
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Cover</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Author</TableHead>
                    <TableHead>Genre</TableHead>
                    <TableHead>Rating</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {books.map((book) => (
                    <TableRow key={book.id}>
                      <TableCell>
                        <img
                          src={book.cover}
                          alt={book.title}
                          className="w-12 h-16 object-cover rounded"
                        />
                      </TableCell>
                      <TableCell className="font-medium">{book.title}</TableCell>
                      <TableCell>{book.author}</TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {book.genre.slice(0, 2).map((g) => (
                            <Badge key={g} variant="secondary" className="text-xs">
                              {g}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center">
                          <span className="mr-1">{book.averageRating}</span>
                          <span className="text-xs text-gray-500">({book.totalReviews})</span>
                        </div>
                      </TableCell>
                      <TableCell>${book.price}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleGenerateSummary(book.id)}
                            disabled={isGeneratingSummary === book.id}
                          >
                            {isGeneratingSummary === book.id ? (
                              <>Generating...</>
                            ) : (
                              <>
                                <Sparkles className="size-3 mr-1" />
                                LLM
                              </>
                            )}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDeleteBook(book.id)}
                          >
                            <Trash2 className="size-4 text-red-600" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
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
                      const book = books.find((b) => b.id === review.bookId);
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
                    const book = books.find((b) => b.id === review.bookId);
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