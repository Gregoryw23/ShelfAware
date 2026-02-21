import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Input } from './ui/input';
import { BookOpen, Clock, Star, Heart, Search, Filter } from 'lucide-react';
import { mockBooks, mockReadingProgress } from '../data/mockData';
import { useNavigate } from 'react-router';

export function Bookshelf() {
  const navigate = useNavigate();
  const [filterGenre, setFilterGenre] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const booksWithProgress = mockBooks.map((book) => ({
    ...book,
    progress: mockReadingProgress.find((p) => p.bookId === book.id),
  }));

  const filteredBooks = booksWithProgress.filter((book) => {
    const matchesSearch = book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      book.author.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesGenre = filterGenre === 'all' || book.genre.includes(filterGenre);
    const matchesStatus =
      filterStatus === 'all' ||
      (filterStatus === 'reading' && book.progress?.status === 'reading') ||
      (filterStatus === 'completed' && book.progress?.status === 'completed') ||
      (filterStatus === 'want-to-read' && book.progress?.status === 'want-to-read');

    return matchesSearch && matchesGenre && matchesStatus;
  });

  const readingBooks = filteredBooks.filter((b) => b.progress?.status === 'reading');
  const completedBooks = filteredBooks.filter((b) => b.progress?.status === 'completed');
  const wantToReadBooks = filteredBooks.filter((b) => b.progress?.status === 'want-to-read');

  const allGenres = Array.from(new Set(mockBooks.flatMap((b) => b.genre)));

  const BookCard = ({ book }: { book: typeof booksWithProgress[0] }) => (
    <Card
      className="cursor-pointer hover:shadow-lg transition-shadow"
      onClick={() => navigate(`/book/${book.id}`)}
    >
      <div className="aspect-[2/3] relative overflow-hidden rounded-t-lg">
        <img src={book.cover} alt={book.title} className="w-full h-full object-cover" />
        {book.progress && book.progress.status === 'reading' && (
          <div className="absolute bottom-0 left-0 right-0 bg-black/75 p-2">
            <div className="flex justify-between items-center text-white text-sm mb-1">
              <span>{book.progress.progress}%</span>
              <Clock className="size-3" />
            </div>
            <Progress value={book.progress.progress} className="h-1" />
          </div>
        )}
      </div>
      <CardContent className="p-4">
        <h3 className="font-semibold line-clamp-1">{book.title}</h3>
        <p className="text-sm text-gray-600 mb-2">{book.author}</p>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center">
            <Star className="size-4 text-yellow-500 mr-1 fill-current" />
            <span className="text-sm">{book.averageRating}</span>
          </div>
          <span className="text-xs text-gray-500">{book.totalReviews} reviews</span>
        </div>
        <div className="flex flex-wrap gap-1">
          {book.genre.slice(0, 2).map((genre) => (
            <Badge key={genre} variant="secondary" className="text-xs">
              {genre}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Bookshelf</h1>
          <p className="text-gray-600">Track your reading journey</p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 size-4" />
              <Input
                placeholder="Search books..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterGenre} onValueChange={setFilterGenre}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by genre" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Genres</SelectItem>
                {allGenres.map((genre) => (
                  <SelectItem key={genre} value={genre}>
                    {genre}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Books</SelectItem>
                <SelectItem value="reading">Currently Reading</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="want-to-read">Want to Read</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Tabs for different book statuses */}
      <Tabs defaultValue="all" className="w-full">
        <TabsList>
          <TabsTrigger value="all">
            All Books ({filteredBooks.length})
          </TabsTrigger>
          <TabsTrigger value="reading">
            <BookOpen className="size-4 mr-2" />
            Reading ({readingBooks.length})
          </TabsTrigger>
          <TabsTrigger value="completed">
            <Star className="size-4 mr-2" />
            Completed ({completedBooks.length})
          </TabsTrigger>
          <TabsTrigger value="want-to-read">
            <Heart className="size-4 mr-2" />
            Want to Read ({wantToReadBooks.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {filteredBooks.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="reading" className="mt-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {readingBooks.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="completed" className="mt-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {completedBooks.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="want-to-read" className="mt-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {wantToReadBooks.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
