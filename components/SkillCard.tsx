import React from 'react';

interface SkillCardProps {
  skill: {
    title: string;
    koreanTitle: string;
    description: string;
  }
}

// Fix: Changed component to be of type React.FC to correctly handle React-specific props like `key`.
const SkillCard: React.FC<SkillCardProps> = ({ skill }) => {
  return (
    <div className="bg-brain-light-navy p-6 rounded-lg shadow-lg hover:shadow-brain-teal/20 transition-shadow duration-300 transform hover:-translate-y-1">
      <h3 className="text-lg font-bold text-brain-teal mb-2">{skill.koreanTitle}</h3>
      <p className="text-sm font-mono text-brain-slate mb-3">{skill.title}</p>
      <p className="text-brain-light-slate text-sm leading-relaxed">{skill.description}</p>
    </div>
  );
}

export default SkillCard;
