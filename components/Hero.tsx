import React from 'react';

export default function Hero() {
  return (
    <section id="hero" className="min-h-screen flex flex-col justify-center animate-fade-in-up" style={{ animationDelay: '100ms' }}>
      <div className="max-w-3xl">
        <h1 className="text-lg md:text-xl font-mono text-brain-teal mb-4">BrainAI AI 교육 프로그램</h1>
        <h2 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-brain-lightest-slate">
          AI 시대를 움직이는<br />새로운 학습 여정
        </h2>
        <p className="mt-6 text-lg md:text-xl text-brain-slate max-w-xl">
          AI의 원리를 이해하고, AI를 협력 파트너로 활용하는 역량을 신장하여<br />미래 사회의 주역으로 성장합니다.
        </p>
        <div className="mt-12">
          <a
            href="https://vimeo.com/showcase/aiforyouth2022"
            target="_blank"
            rel="noopener noreferrer"
            className="text-brain-teal border border-brain-teal rounded px-8 py-4 text-lg font-bold hover:bg-brain-teal/10 transition-all duration-300"
          >
            핵심 프로젝트 보기
          </a>
        </div>
      </div>
    </section>
  );
};