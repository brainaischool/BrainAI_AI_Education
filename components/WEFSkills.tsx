import React from 'react';
import SkillCard from './SkillCard';

interface Skill {
  title: string;
  koreanTitle: string;
  description: string;
}

const skills: Skill[] = [
  {
    title: 'Analytical Thinking',
    koreanTitle: '분석적 사고',
    description: '센서 데이터를 분석하고 주행 상황을 판단하며, 데이터 속에서 의미 있는 패턴을 찾아 효율적인 판단 로직을 설계합니다.'
  },
  {
    title: 'Resilience, Flexibility, and Agility',
    koreanTitle: '회복탄력성, 유연성, 민첩성',
    description: 'AI 모델의 센서 오류, 코딩 버그 등 예상치 못한 문제에 직면했을 때, 좌절하지 않고 유연하게 대처하는 능력을 기릅니다.'
  },
  {
    title: 'Leadership and Social Influence',
    koreanTitle: '리더십과 사회적 영향력',
    description: '팀 단위 프로젝트에서 협력을 통해 최적의 주행 전략을 논의하고 합의하며 리더십과 긍정적 영향력을 발휘합니다.'
  },
  {
    title: 'Creative Thinking',
    koreanTitle: '창의적 사고',
    description: "주어진 문제를 넘어 '이 AI를 어디에 더 응용할 수 있을까?'를 고민하며 새로운 AI+X 융합 아이디어를 발상합니다."
  },
  {
    title: 'Motivation and Self-awareness',
    koreanTitle: '동기부여 및 자기 인식',
    description: '자신의 AI 모델의 성공/실패 과정을 보며 스스로 학습 여정을 성찰하고, 강점과 약점을 인식하며 능동적으로 발전 방향을 탐색합니다.'
  },
  {
    title: 'Technological Literacy',
    koreanTitle: '기술 소양',
    description: 'AI 이론, 센서, 코딩까지 자율주행 기술 전반을 직접 체험하고 이해하며 미래 기술에 대한 실질적인 소양과 자신감을 확보합니다.'
  }
];

export default function WEFSkills() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {skills.map(skill => (
        <SkillCard key={skill.title} skill={skill} />
      ))}
    </div>
  );
};
