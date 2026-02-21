import React from 'react';
import { Link, useLocation } from 'react-router';
import { User, Library, MessageSquare, LogOut, Shield } from 'lucide-react';
import { Button } from './ui/button';
import logoImage from 'figma:asset/08044afe8eb8f9700793bdbb3ce5779e85ca56f7.png';

interface LayoutProps {
  children: React.ReactNode;
  isAdmin: boolean;
  onLogout: () => void;
}

export function Layout({ children, isAdmin, onLogout }: LayoutProps) {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const navItems = isAdmin
    ? [
        { path: '/admin', icon: Shield, label: 'Admin Panel' },
        { path: '/bookshelf', icon: Library, label: 'Bookshelf' },
      ]
    : [
        { path: '/bookshelf', icon: Library, label: 'Bookshelf' },
        { path: '/chatbot', icon: MessageSquare, label: 'Chatbot' },
        { path: '/profile', icon: User, label: 'Profile' },
      ];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/bookshelf" className="flex items-center">
              <img src={logoImage} alt="Shelf Aware" className="h-10" />
            </Link>

            <nav className="flex items-center space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link key={item.path} to={item.path}>
                    <Button
                      variant={isActive(item.path) ? 'default' : 'ghost'}
                      className="flex items-center"
                    >
                      <Icon className="size-4 mr-2" />
                      {item.label}
                    </Button>
                  </Link>
                );
              })}
              <Button variant="ghost" onClick={onLogout} className="flex items-center">
                <LogOut className="size-4 mr-2" />
                Logout
              </Button>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">{children}</main>
    </div>
  );
}