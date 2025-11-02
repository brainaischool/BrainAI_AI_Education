import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-brain-dark border-t border-brain-navy py-6 text-center text-brain-slate">
      <div className="container mx-auto px-6">
        <p className="mt-2 text-sm">© {new Date().getFullYear()} BrainAI Co.,Ltd. All Rights Reserved.</p>
        <p className="text-sm">문의처: contact@brainai.co.kr | 웹사이트: brainai.kr</p>
      </div>
    </footer>
  );
};