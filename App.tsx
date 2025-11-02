import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import About from './components/About';
import ProgramDetails from './components/ProgramDetails';
import AutonomousCarProject from './components/AutonomousCarProject';
import AIXProject from './components/AIXProject';
import MultiSorterProject from './components/MultiSorterProject';
import StudentExchange from './components/StudentExchange';
import Footer from './components/Footer';

export default function App() {
  const [currentView, setCurrentView] = useState(window.location.hash || '#home');

  useEffect(() => {
    const handleHashChange = () => {
      const newHash = window.location.hash || '#home';
      setCurrentView(newHash);
      window.scrollTo(0, 0);
    };

    window.addEventListener('hashchange', handleHashChange, false);

    // Initial load check
    handleHashChange();

    return () => {
      window.removeEventListener('hashchange', handleHashChange, false);
    };
  }, []);

  const isHomePage = currentView === '#home' || currentView === '#hero';

  const renderHomePageContent = () => (
    <>
      <Hero />
      <About />
      <ProgramDetails />
      <AIXProject />
      <MultiSorterProject />
      <AutonomousCarProject />
      <StudentExchange />
    </>
  );
  
  const renderSinglePageContent = () => {
      const pageWrapperClass = "pt-24 min-h-screen";
      
      const pages = {
          '#about': <About />,
          '#programs': <ProgramDetails />,
          '#autonomous-car': <AutonomousCarProject />,
          '#aix': <AIXProject />,
          '#multi-sorter': <MultiSorterProject />,
          '#student-exchange': <StudentExchange />,
      };

      return (
        <div className={pageWrapperClass}>
            {Object.entries(pages).map(([hash, Component]) => (
                <div key={hash} style={{ display: currentView === hash ? 'block' : 'none' }}>
                    {Component}
                </div>
            ))}
        </div>
      );
  };


  return (
    <div className="bg-brain-dark text-brain-light-slate font-sans leading-relaxed">
      <Header />
      <main className="container mx-auto px-6 md:px-10 lg:px-20">
        {isHomePage ? renderHomePageContent() : renderSinglePageContent()}
      </main>
      <Footer />
    </div>
  );
};