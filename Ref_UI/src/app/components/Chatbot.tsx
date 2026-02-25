import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Send, Bot, User, Sparkles, Heart } from 'lucide-react';
import { mockBooks, emotionTags } from '../data/mockData';
import { ChatMessage } from '../types';

export function Chatbot() {
  const [messages, setMessages] = useState<ChatMessage[]>([
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

  const generateResponse = (userMessage: string, emotions: string[]) => {
    // Simple mock AI responses based on emotions
    const emotionLower = emotions.map((e) => e.toLowerCase());
    
    if (emotionLower.includes('sad') || emotionLower.includes('melancholic')) {
      const recommendations = mockBooks.filter((b) => 
        b.genre.includes('Fantasy') || b.genre.includes('Biography/Memoir')
      ).slice(0, 3);
      return `I understand you're feeling ${emotions.join(', ')}. Here are some books that might help:\n\n${recommendations.map(b => `• "${b.title}" by ${b.author} - ${b.abstract.substring(0, 100)}...`).join('\n\n')}`;
    }
    
    if (emotionLower.includes('motivated') || emotionLower.includes('inspired')) {
      const recommendations = mockBooks.filter((b) => 
        b.genre.includes('Psychology/Self-Help') || b.genre.includes('Biography/Memoir')
      ).slice(0, 3);
      return `Great energy! Here are some motivational reads:\n\n${recommendations.map(b => `• "${b.title}" by ${b.author} - ${b.abstract.substring(0, 100)}...`).join('\n\n')}`;
    }
    
    if (emotionLower.includes('curious') || emotionLower.includes('adventurous')) {
      const recommendations = mockBooks.filter((b) => 
        b.genre.includes('Mystery/Thriller') || b.genre.includes('Science Fiction')
      ).slice(0, 3);
      return `Perfect! Here are some thrilling reads for your curious mind:\n\n${recommendations.map(b => `• "${b.title}" by ${b.author} - ${b.abstract.substring(0, 100)}...`).join('\n\n')}`;
    }

    return `Based on your emotions (${emotions.join(', ')}), I'd recommend exploring these books:\n\n${mockBooks.slice(0, 3).map(b => `• "${b.title}" by ${b.author} - A ${b.genre[0]} book rated ${b.averageRating} stars.`).join('\n\n')}\n\nWould you like to know more about any of these?`;
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim() && selectedEmotions.length === 0) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage || `Feeling: ${selectedEmotions.join(', ')}`,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const response = generateResponse(
        inputMessage,
        selectedEmotions.length > 0 ? selectedEmotions : ['neutral']
      );
      
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
      setSelectedEmotions([]);
    }, 1500);
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