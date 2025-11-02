import React, { useState, useEffect } from 'react';

export default function Header() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: '소개', href: '#about' },
    { name: '프로그램', href: '#programs' },
    { name: 'AI + X', href: '#aix' },
    { name: '자동분류 챌린지', href: '#multi-sorter' },
    { name: '자율주행 챌린지', href: '#autonomous-car' },
    { name: '학생 교류', href: '#student-exchange' },
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled ? 'bg-brain-dark/80 backdrop-blur-sm shadow-lg' : 'bg-transparent'
      }`}
    >
      <nav className="container mx-auto px-6 md:px-10 lg:px-20 py-4 flex justify-between items-center">
        <a href="#home" className="text-2xl font-bold text-brain-teal">
          BrainAI
        </a>
        <div className="hidden md:flex items-center space-x-6">
          {navLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              className="text-sm text-brain-lightest-slate hover:text-brain-teal transition-colors duration-300 whitespace-nowrap"
            >
              {link.name}
            </a>
          ))}
        </div>
        {/* Mobile menu could be added here */}
      </nav>
    </header>
  );
};