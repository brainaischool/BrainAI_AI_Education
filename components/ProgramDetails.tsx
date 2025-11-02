import React from 'react';
import SectionTitle from './SectionTitle';
import ProgramCard from './ProgramCard';

export default function ProgramDetails() {
  const programs = [
    {
      title: 'AI + X (다양한 산업 접목)',
      description: '의료, 환경, 예술 등 다양한 분야와 AI를 융합하는 방법을 No Code, Low Code 기반으로 학습합니다.',
      link: '#aix',
      imageSrc: 'https://picsum.photos/seed/aix/600/400',
    },
    {
      title: 'BrainAI Multi Sorter 자동분류 챌린지',
      description: 'AI + Physical 컴퓨팅: 실제 하드웨어(BrainAI Multi Sorter)를 제어하며 자동분류 AI 기술을 현실 세계에 적용합니다.',
      link: '#multi-sorter',
      imageSrc: 'https://picsum.photos/seed/sorter/600/400',
    },
    {
      title: 'BrainAI Car 자율주행 챌린지',
      description: 'AI + Physical 컴퓨팅: 실제 하드웨어(BrainAI Car)를 제어하며 자율주행 AI 기술을 현실 세계에 적용합니다.',
      link: '#autonomous-car',
      imageSrc: 'https://picsum.photos/seed/autocar/600/400',
    },
    {
      title: 'South Korea & Singapore Student Exchange',
      description: '싱가포르 학생들과의 교류를 통해 글로벌 AI 역량을 키우고 국제적 감각을 함양합니다.',
      link: '#student-exchange',
      imageSrc: 'https://picsum.photos/seed/exchange/600/400',
    },
  ];

  return (
    <section id="programs" className="py-24 animate-fade-in-up" style={{ animationDelay: '300ms' }}>
      <SectionTitle number="02" title="BrainAI AI 교육 프로그램" />
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
        {programs.map((program) => (
          <ProgramCard key={program.title} {...program} />
        ))}
      </div>
       <div className="text-center mt-12">
           <p className="text-brain-slate">
            BrainAI AI 교육 프로그램은 글로벌 기업 인텔의 AI 교육 프로그램인{' '}
            <a href="https://www.intel.com/content/www/us/en/corporate/artificial-intelligence/digital-readiness-ai-for-youth.html" target="_blank" rel="noopener noreferrer" className="text-brain-teal hover:underline font-bold">
              Intel® AI for Youth Program
            </a>
            과{' '}<br />
            <a href="https://aistudio.google.com/" target="_blank" rel="noopener noreferrer" className="text-brain-teal hover:underline font-bold">
              Google AI Studio
            </a>
            를 기반으로 합니다.
           </p>
       </div>
    </section>
  );
};