import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Avatar, AvatarFallback } from './ui/avatar';
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from './ui/carousel';
import { Send, Bot, User, Sparkles, Heart } from 'lucide-react';
import { emotionTags } from '../data/mockData';
import { ChatMessage } from '../types';
import { apiService, ChatBookRecommendation } from '../services/api';

interface UIChatMessage extends ChatMessage {
  recommendedBooks?: ChatBookRecommendation[];
  followUpQuestions?: string[];
}

export function Chatbot() {
  const [messages, setMessages] = useState<UIChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hi! I'm your emotion-aware book assistant. How are you feeling today? I can help you find the perfect book based on your emotions and preferences.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedEmotions, setSelectedEmotions] = useState<string[]>([]);
  const [isTyping, setIsTyping] = useState(false);

  const toggleEmotion = (emotion: string) => {
    setSelectedEmotions((prev) =>
      prev.includes(emotion) ? prev.filter((e) => e !== emotion) : [...prev, emotion]
    );
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() && selectedEmotions.length === 0) return;

    const outgoingMessage = inputMessage.trim() || `Feeling: ${selectedEmotions.join(', ')}`;
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: outgoingMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      const result = await apiService.chat({ message: outgoingMessage });
      const aiMessage: UIChatMessage = {
        id: `${Date.now()}-assistant`,
        role: 'assistant',
        content: result.response,
        timestamp: new Date().toISOString(),
        recommendedBooks: result.books,
        followUpQuestions: result.follow_up_questions,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error calling chatbot API:', error);
      const fallbackMessage: ChatMessage = {
        id: `${Date.now()}-assistant-error`,
        role: 'assistant',
        content: 'I could not reach the chatbot service right now. Please try again in a moment.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, fallbackMessage]);
    } finally {
      setIsTyping(false);
      setSelectedEmotions([]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Book Recommendation Chatbot</h1>
        <p className="text-gray-600">Get personalized book recommendations based on your emotions</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Chat Interface */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bot className="size-5 mr-2 text-purple-600" />
              Chat with AI Assistant
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col h-[600px]">
              {/* Messages */}
              <ScrollArea className="flex-1 pr-4 mb-4">
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex items-start gap-3 ${
                        message.role === 'user' ? 'flex-row-reverse' : ''
                      }`}
                    >
                      <Avatar className="size-8">
                        <AvatarFallback>
                          {message.role === 'user' ? <User className="size-4" /> : <Bot className="size-4" />}
                        </AvatarFallback>
                      </Avatar>
                      <div
                        className={`flex-1 rounded-lg p-3 ${
                          message.role === 'user'
                            ? 'bg-purple-600 text-white ml-12'
                            : 'bg-gray-100 mr-12'
                        }`}
                      >
                        <p className="text-sm whitespace-pre-line">{message.content}</p>

                        {message.role === 'assistant' && message.recommendedBooks && message.recommendedBooks.length > 0 && (
                          <div className="mt-3 space-y-2">
                            <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                              Recommended books
                            </p>
                            <Carousel
                              opts={{ align: 'start', loop: false }}
                              className="w-full px-8"
                            >
                              <CarouselContent>
                                {message.recommendedBooks.map((book) => (
                                  <CarouselItem key={book.book_id} className="basis-[155px] sm:basis-[175px]">
                                    <div className="rounded-md border bg-white overflow-hidden">
                                      <img
                                        src={book.cover_image_url || 'https://via.placeholder.com/120x180?text=No+Cover'}
                                        alt={book.title}
                                        className="w-full h-40 object-cover"
                                      />
                                      <div className="p-2">
                                        <p className="text-xs font-semibold text-gray-900 line-clamp-2" title={book.title}>
                                          {book.title}
                                        </p>
                                      </div>
                                    </div>
                                  </CarouselItem>
                                ))}
                              </CarouselContent>
                              <CarouselPrevious className="left-0" />
                              <CarouselNext className="right-0" />
                            </Carousel>
                          </div>
                        )}

                        {message.role === 'assistant' && message.followUpQuestions && message.followUpQuestions.length > 0 && (
                          <div className="mt-3">
                            <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
                              Follow-up questions
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {message.followUpQuestions.map((question, idx) => (
                                <button
                                  key={`${message.id}-followup-${idx}`}
                                  type="button"
                                  onClick={() => setInputMessage(question)}
                                  className="text-xs bg-white border border-gray-200 rounded-full px-3 py-1 text-gray-700 hover:bg-gray-50"
                                >
                                  {question}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        <span className="text-xs opacity-70 mt-1 block">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))}

                  {isTyping && (
                    <div className="flex items-start gap-3">
                      <Avatar className="size-8">
                        <AvatarFallback>
                          <Bot className="size-4" />
                        </AvatarFallback>
                      </Avatar>
                      <div className="bg-gray-100 rounded-lg p-3">
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>

              {/* Input Area */}
              <div className="space-y-3">
                {selectedEmotions.length > 0 && (
                  <div className="flex flex-wrap gap-2 p-2 bg-purple-50 rounded-lg">
                    <span className="text-sm text-gray-600">Selected emotions:</span>
                    {selectedEmotions.map((emotion) => (
                      <Badge key={emotion} variant="default" className="text-xs">
                        {emotion}
                      </Badge>
                    ))}
                  </div>
                )}
                <div className="flex gap-2">
                  <Input
                    placeholder="Type your message or select emotions..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    className="flex-1"
                  />
                  <Button onClick={handleSendMessage} disabled={isTyping}>
                    <Send className="size-4" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Emotion Selector */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Heart className="size-5 mr-2 text-pink-600" />
                How are you feeling?
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">
                Select emotions to get personalized book recommendations
              </p>
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
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Sparkles className="size-5 mr-2 text-yellow-600" />
                Quick Tips
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>• Select emotions that match your current mood</li>
                <li>• Ask about specific genres or authors</li>
                <li>• Request books similar to ones you've enjoyed</li>
                <li>• Tell me what you want to feel (e.g., "I want to feel inspired")</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}