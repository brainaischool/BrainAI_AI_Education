import React from 'react';
import SectionTitle from './SectionTitle';
import CheckIcon from './CheckIcon';
import SkillCard from './SkillCard';

export default function AIXProject() {
    const projectCycleSteps = [
        { icon: '💡', title: '문제 발견 및 아이디어', description: '자신이 관심 있는 분야(의료, 환경, 예술 등)에서 AI로 해결할 수 있는 문제는 무엇인가?' },
        { icon: '💾', title: '데이터 수집 및 계획', description: '아이디어에 필요한 데이터는 어디서, 어떻게 구할 것인가? (예: 공공 데이터, 웹 크롤링)' },
        { icon: '🛠️', title: '데이터 가공', description: '데이터의 특징을 파악하고, AI 모델 학습에 적합한 형태로 가공합니다.' },
        { icon: '🧠', title: 'AI 모델링', description: 'No Code/Low Code 도구를 활용해 아이디어를 빠르게 AI 모델로 구현합니다.' },
        { icon: '📈', title: '검증 및 개선', description: '만들어진 AI 모델이 문제를 효과적으로 해결하는지 검증하고 개선합니다.' },
        { icon: '🚀', title: '프로토타입 및 발표', description: '프로토타입을 제작하여 아이디어를 시각화하고, 다른 사람들에게 제안/발표합니다.' },
    ];

    const outcomes = [
        {
            title: "창의적 융합 사고 능력 배양",
            description: "AI 기술을 자신의 관심 분야(의료, 예술, 환경 등)와 결합하는 경험을 통해, 경계를 넘나드는 창의적 문제 해결 능력을 갖추게 됩니다."
        },
        {
            title: "No Code/Low Code AI 개발 역량 확보",
            description: "복잡한 코딩 없이도 아이디어를 빠르게 프로토타입핑하고 구현할 수 있는 최신 AI 개발 도구 활용 능력을 습득합니다."
        },
        {
            title: "사회적 문제 해결을 위한 AI 프로젝트 기획",
            description: "단순한 기술 학습을 넘어, 사회에 긍정적인 영향을 미칠 수 있는 'Social Impact' AI 프로젝트를 직접 기획하고 구체화하는 경험을 합니다."
        }
    ];

    const wefSkills = [
        {
            title: 'Analytical Thinking',
            koreanTitle: '분석적 사고',
            description: '다양한 산업 분야의 문제를 분석하여 데이터 기반으로 해결 가능한 AI 프로젝트를 정의하고, 아이디어의 실현 가능성을 논리적으로 검토합니다.'
        },
        {
            title: 'Creative Thinking',
            koreanTitle: '창의적 사고',
            description: "주어진 문제를 넘어 '이 AI를 어디에 더 응용할 수 있을까?'를 고민하며 새로운 AI+X 융합 아이디어를 발상합니다."
        },
        {
            title: 'Resilience, Flexibility, and Agility',
            koreanTitle: '회복탄력성, 유연성, 민첩성',
            description: '아이디어를 프로토타입으로 만드는 과정에서 발생하는 기술적 난관과 예상치 못한 결과에 좌절하지 않고, 유연한 사고로 대안을 찾아내고 민첩하게 계획을 수정합니다.'
        },
        {
            title: 'Leadership and Social Influence',
            koreanTitle: '리더십과 사회적 영향력',
            description: '사회 문제를 해결하는 자신의 AI 프로젝트 아이디어를 설득력 있게 제시하고, 팀원이나 동료의 협력을 이끌어내며 긍정적인 영향력을 발휘하는 경험을 합니다.'
        }
    ];

    return (
        <section id="aix" className="py-24 animate-fade-in-up" style={{ animationDelay: '400ms' }}>
            <SectionTitle number="03" title="AI + X (다양한 산업 접목)" />
            
            <div className="mb-20">
                <h4 className="text-2xl font-bold text-brain-lightest-slate text-center mb-10">AI + X 융합 프로젝트와 WEF 미래 핵심역량의 만남</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {wefSkills.map(skill => (
                        <SkillCard key={skill.title} skill={skill} />
                    ))}
                </div>
            </div>

            <div className="mb-20">
                <h4 className="text-2xl font-bold text-brain-lightest-slate text-center mb-10">아이디어를 현실로 만드는 6단계</h4>
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
                 <p className="text-center text-lg text-brain-light-slate mb-12">AI를 도구로 사용하여, 자신의 아이디어를 현실로 만들고 세상을 긍정적으로 변화시키는 경험을 제공합니다.</p>
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
                     <p className="font-bold text-brain-lightest-slate">최종 결과물: 사회 문제 해결을 위한 AI 서비스 프로토타입 및 사업 계획서</p>
                 </div>
            </div>

        </section>
    );
};