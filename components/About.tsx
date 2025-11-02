import React from 'react';
import SectionTitle from './SectionTitle';

export default function About() {
  const mottoPoints = [
    "첫째, 학생들은 이전 세대와 다릅니다.",
    "둘째, AI 기술은 예측할 수 없는 속도로 발전하고 있습니다.",
    "셋째, 교육자들은 이 빠른 발전에 발맞추어야 합니다.",
    "넷째, AI 기반 산업에 학생들을 대비 시키기 위한 효과적인 전략이 필요합니다.",
  ];

  return (
    <section id="about" className="py-24 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
      <SectionTitle number="01" title="우리의 비전과 철학" />
      <div className="grid md:grid-cols-2 gap-10">
        <div>
          <h3 className="text-2xl font-bold text-brain-lightest-slate mb-4">비전</h3>
          <p className="mb-4">
            AI의 원리를 이해하고 AI를 협력 파트너로 활용하는 역량을 신장하여, 학생들이 미래 사회의 변화를 주도하는 인재로 성장하도록 돕습니다.
          </p>
           <a href="https://www.weforum.org/publications/the-future-of-jobs-report-2025/" target="_blank" rel="noopener noreferrer" className="text-brain-teal hover:underline leading-relaxed">
            WEF(세계 경제 포럼, World Economy Forum)
            <br />
            미래 핵심역량
            <br />
            The Future of Jobs Report 2025 &rarr;
          </a>
          <h3 className="text-2xl font-bold text-brain-lightest-slate mt-8 mb-4">방법론: PBL</h3>
          <p>
            단순한 지식 전달을 넘어, 학생들이 실제 사회 문제를 해결하는 'Social Impact AI Project'를 직접 기획하고 만들어가는 프로젝트 기반 학습(Project Based Learning)을 추구합니다.
          </p>
        </div>
        <div>
          <div className="bg-brain-navy p-6 rounded-lg shadow-lg">
            <h3 className="text-xl font-bold text-brain-teal mb-3 font-mono">모토: 학생이 미래다.</h3>
            <p className="mb-4">우리 학생들을 AI 중심의 현실에 대비 시키는 것은 중요한 과제입니다. 우리는 4가지 측면에서 접근합니다.</p>
            <ul className="space-y-2">
              {mottoPoints.map((point, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-brain-teal mr-2">✓</span>
                  <span className="text-brain-light-slate">{point}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
};