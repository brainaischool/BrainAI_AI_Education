import React from 'react';
import SectionTitle from './SectionTitle';
import CheckIcon from './CheckIcon';
import SkillCard from './SkillCard';

export default function MultiSorterProject() {
    const projectCycleSteps = [
        { icon: '🎯', title: '문제 정의', description: '어떤 객체들을, 어떤 기준으로 자동 분류할 것인가? (예: 재활용품 종류별 분류)' },
        { icon: '📸', title: '데이터 획득', description: '객체 이미지 데이터를 수집하고, 분류 기준에 맞게 라벨링합니다. (예: 스마트폰 카메라 활용)' },
        { icon: '✨', title: '데이터 탐색 및 전처리', description: '다양한 조건의 이미지 데이터 품질을 높이고, 모델 학습에 최적화합니다.' },
        { icon: '🤖', title: '모델링', description: '컴퓨터 비전(Teachable Machine 등)을 활용해 객체 분류 AI 모델을 훈련시킵니다.' },
        { icon: '💯', title: '모델 평가 및 최적화', description: 'AI 모델의 분류 정확도를 평가하고, 실제 하드웨어 오작동 원인을 분석하여 개선합니다.' },
        { icon: '⚙️', title: '배포 및 자동화', description: '학습된 모델을 Multi Sorter에 탑재하여 실시간 자동 분류 시스템을 완성합니다.' },
    ];

    const outcomes = [
        {
            title: "컴퓨터 비전 및 자동화 시스템 이해",
            description: "이미지 인식 AI 모델을 실제 하드웨어(컨베이어 벨트, 서보 모터)와 연동하며, 스마트 팩토리와 같은 자동화 시스템의 핵심 원리를 체득합니다."
        },
        {
            title: "AI 모델의 물리적 세계 제어 경험",
            description: "디지털 공간에 머물던 AI 모델이 현실 세계의 객체를 분류하고 움직이는 과정을 직접 구현하며, AI의 물리적 적용 능력을 함양합니다."
        },
        {
            title: "문제 해결을 위한 시스템 최적화",
            description: "분류 정확도, 속도 등 주어진 목표를 달성하기 위해 AI 모델과 하드웨어를 함께 최적화하는 과정을 통해 공학적 문제 해결 능력을 기릅니다."
        }
    ];

    const wefSkills = [
        {
            title: 'Analytical Thinking',
            koreanTitle: '분석적 사고',
            description: 'AI 모델의 분류 정확도, 시스템의 처리 속도 등 성능 지표를 데이터 기반으로 분석하고, 병목 현상을 찾아 시스템을 최적화합니다.'
        },
        {
            title: 'Technological Literacy',
            koreanTitle: '기술 소양',
            description: '컴퓨터 비전 AI 이론, 하드웨어 센서, 제어 프로그래밍까지 자동화 시스템의 기술 전반을 직접 체험하고 이해하며 실질적인 기술 소양을 확보합니다.'
        },
        {
            title: 'Resilience, Flexibility, and Agility',
            koreanTitle: '회복탄력성, 유연성, 민첩성',
            description: 'AI 모델의 오작동, 하드웨어 센서 오류 등 예측 불가능한 문제에 직면했을 때, 원인을 체계적으로 분석하고 해결책을 찾아 적용하는 능력을 기릅니다.'
        },
        {
            title: 'Leadership and Social Influence',
            koreanTitle: '리더십과 사회적 영향력',
            description: '팀 프로젝트에서 자동화 시스템의 목표(정확도, 속도) 달성을 위해 역할을 분담하고, 기술적 의사결정 과정을 주도하며 팀의 시너지를 이끌어냅니다.'
        }
    ];

    return (
        <section id="multi-sorter" className="py-24 animate-fade-in-up" style={{ animationDelay: '500ms' }}>
            <SectionTitle number="04" title="BrainAI Multi Sorter 자동분류 챌린지" />
            
            <div className="mb-20">
                <h4 className="text-2xl font-bold text-brain-lightest-slate text-center mb-10">자동분류 챌린지와 WEF 미래 핵심역량의 만남</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {wefSkills.map(skill => (
                        <SkillCard key={skill.title} skill={skill} />
                    ))}
                </div>
            </div>

            <div className="mb-20">
                <h4 className="text-2xl font-bold text-brain-lightest-slate text-center mb-10">AI 자동화 시스템 구축 6단계</h4>
                <div className="relative max-w-4xl mx-auto mt-10">
                    <div className="hidden lg:block absolute top-1/2 left-0 w-full h-0.5 bg-brain-light-navy -translate-y-1/2"></div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {projectCycleSteps.map((step, index) => (
                        <div key={index} className="lg:col-span-1 md:col-span-1 col-span-2">
                            <div className="relative bg-brain-navy p-6 rounded-lg shadow-lg z-10 text-center flex flex-col items-center">
                            <div className="text-4xl mb-4">{step.icon}</div>
                            <h3 className="text-lg font-bold text-brain-teal mb-2">
                                <span className="font-mono">{index + 1}.</span> {step.title}
                            </h3>
                            <p className="text-brain-slate text-sm">{step.description}</p>
                            </div>
                        </div>
                        ))}
                    </div>
                </div>
            </div>

            <div>
                 <h4 className="text-2xl font-bold text-brain-lightest-slate text-center mb-4">교육 목표 및 기대 효과</h4>
                 <p className="text-center text-lg text-brain-light-slate mb-12">BrainAI는 AI를 통해 현실의 물리적인 문제를 해결하는 실질적인 역량을 제공합니다.</p>
                 <div className="max-w-4xl mx-auto space-y-8">
                    {outcomes.map((outcome, index) => (
                        <div key={index} className="flex items-start space-x-4 p-6 bg-brain-navy rounded-lg">
                            <CheckIcon />
                            <div>
                                <h3 className="text-xl font-bold text-brain-lightest-slate">{outcome.title}</h3>
                                <p className="mt-1 text-brain-slate">{outcome.description}</p>
                            </div>
                        </div>
                    ))}
                 </div>
                 <div className="max-w-4xl mx-auto mt-10 text-center p-6 bg-brain-light-navy rounded-lg">
                     <p className="font-bold text-brain-lightest-slate">최종 결과물: 특정 객체 자동 분류 시스템 및 성능 개선 보고서</p>
                 </div>
            </div>

        </section>
    );
};