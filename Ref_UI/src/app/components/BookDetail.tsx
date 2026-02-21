import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Textarea } from './ui/textarea';
import { Slider } from './ui/slider';
import { Separator } from './ui/separator';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Star, Heart, ArrowLeft, ThumbsUp, Calendar } from 'lucide-react';
import { mockBooks, mockReadingProgress, mockReviews, emotionTags } from '../data/mockData';
import { toast } from 'sonner';

export function BookDetail() {
  const { bookId } = useParams();
  const navigate = useNavigate();
  const book = mockBooks.find((b) => b.id === bookId);
  const progress = mockReadingProgress.find((p) => p.bookId === bookId);
  const bookReviews = mockReviews.filter((r) => r.bookId === bookId);

  const [myRating, setMyRating] = useState(0);
  const [reviewText, setReviewText] = useState('');
  const [selectedEmotions, setSelectedEmotions] = useState<string[]>([]);
  const [readingProgress, setReadingProgress] = useState(progress?.progress || 0);

  if (!book) {
    return <div>Book not found</div>;
  }

  const toggleEmotion = (emotion: string) => {
    setSelectedEmotions((prev) =>
      prev.includes(emotion) ? prev.filter((e) => e !== emotion) : [...prev, emotion]
    );
  };

  const handleSubmitReview = () => {
    if (myRating === 0) {
      toast.error('Please select a rating');
      return;
    }
    if (selectedEmotions.length === 0) {
      toast.error('Please select at least one emotion');
      return;
    }
    toast.success('Review submitted successfully!');
    setReviewText('');
    setMyRating(0);
    setSelectedEmotions([]);
  };

  const handleUpdateProgress = () => {
    toast.success(`Progress updated to ${readingProgress}%`);
  };

  return (
    <div className="space-y-6">
      <Button variant="ghost" onClick={() => navigate('/bookshelf')} className="mb-4">
        <ArrowLeft className="size-4 mr-2" />
        Back to Bookshelf
      </Button>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Book Cover and Info */}
        <div className="md:col-span-1">
          <Card>
            <CardContent className="p-6">
              <img
                src={book.cover}
                alt={book.title}
                className="w-full rounded-lg shadow-lg mb-4"
              />
              <h1 className="text-2xl font-bold mb-2">{book.title}</h1>
              <p className="text-gray-600 mb-4">{book.author}</p>

              <div className="flex items-center mb-4">
                <Star className="size-5 text-yellow-500 mr-2 fill-current" />
                <span className="text-xl font-semibold">{book.averageRating}</span>
                <span className="text-sm text-gray-500 ml-2">
                  ({book.totalReviews} reviews)
                </span>
              </div>

              <div className="flex flex-wrap gap-2 mb-4">
                {book.genre.map((genre) => (
                  <Badge key={genre} variant="secondary">
                    {genre}
                  </Badge>
                ))}
              </div>

              <Separator className="my-4" />

              <div className="space-y-2">
                <p className="text-sm text-gray-600">
                  <strong>Price:</strong> ${book.price}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Condition:</strong> {book.condition}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="md:col-span-2 space-y-6">
          {/* Reading Progress */}
          <Card>
            <CardHeader>
              <CardTitle>Reading Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Progress: {readingProgress}%</span>
                  {progress && (
                    <span className="text-xs text-gray-500">
                      Last read: {new Date(progress.lastRead).toLocaleDateString()}
                    </span>
                  )}
                </div>
                <Progress value={readingProgress} className="h-2" />
                <Slider
                  value={[readingProgress]}
                  onValueChange={(value) => setReadingProgress(value[0])}
                  max={100}
                  step={1}
                  className="py-4"
                />
                <Button onClick={handleUpdateProgress} className="w-full">
                  Update Progress
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* About the Book */}
          <Card>
            <CardHeader>
              <CardTitle>About this Book</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700">{book.abstract}</p>
            </CardContent>
          </Card>

          {/* Write Review */}
          <Card>
            <CardHeader>
              <CardTitle>Write a Review</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Rating */}
              <div>
                <label className="block text-sm font-medium mb-2">Your Rating</label>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setMyRating(star)}
                      className="focus:outline-none"
                    >
                      <Star
                        className={`size-8 ${
                          star <= myRating
                            ? 'text-yellow-500 fill-current'
                            : 'text-gray-300'
                        }`}
                      />
                    </button>
                  ))}
                </div>
              </div>

              {/* Emotions */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  How did this book make you feel?
                </label>
                <div className="flex flex-wrap gap-2">
                  {emotionTags.map((emotion) => (
                    <Badge
                      key={emotion}
                      variant={selectedEmotions.includes(emotion) ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => toggleEmotion(emotion)}
                    >
                      {emotion}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Review Text */}
              <div>
                <label className="block text-sm font-medium mb-2">Your Review</label>
                <Textarea
                  placeholder="Share your thoughts about this book..."
                  value={reviewText}
                  onChange={(e) => setReviewText(e.target.value)}
                  rows={4}
                />
              </div>

              <Button onClick={handleSubmitReview} className="w-full">
                Submit Review
              </Button>
            </CardContent>
          </Card>

          {/* Existing Reviews */}
          <Card>
            <CardHeader>
              <CardTitle>Reviews ({bookReviews.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {bookReviews.map((review) => (
                <div key={review.id} className="border-b pb-4 last:border-b-0">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center">
                      <Avatar className="size-10 mr-3">
                        <AvatarFallback>U</AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="flex items-center">
                          {Array.from({ length: 5 }).map((_, i) => (
                            <Star
                              key={i}
                              className={`size-4 ${
                                i < review.rating
                                  ? 'text-yellow-500 fill-current'
                                  : 'text-gray-300'
                              }`}
                            />
                          ))}
                        </div>
                        <div className="flex items-center text-xs text-gray-500 mt-1">
                          <Calendar className="size-3 mr-1" />
                          {new Date(review.date).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                    {review.moderated && (
                      <Badge variant="secondary" className="text-xs">
                        Verified
                      </Badge>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2 mb-2">
                    {review.emotion.map((emotion) => (
                      <Badge key={emotion} variant="outline" className="text-xs">
                        <Heart className="size-3 mr-1" />
                        {emotion}
                      </Badge>
                    ))}
                  </div>

                  <p className="text-gray-700 mb-2">{review.content}</p>

                  <button className="flex items-center text-sm text-gray-500 hover:text-gray-700">
                    <ThumbsUp className="size-4 mr-1" />
                    Helpful ({review.helpful})
                  </button>
                </div>
              ))}

              {bookReviews.length === 0 && (
                <p className="text-center text-gray-500">No reviews yet. Be the first to review!</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
