import React from 'react';

interface SectionTitleProps {
  number: string;
  title: string;
}

export default function SectionTitle({ number, title }: SectionTitleProps) {
  return (
    <h2 className="text-3xl font-bold text-brain-lightest-slate mb-8 flex items-center">
        <span className="text-brain-teal font-mono mr-3 text-2xl">{number}.</span> {title}
        <span className="flex-grow h-px bg-brain-light-navy ml-4"></span>
    </h2>
  );
}
