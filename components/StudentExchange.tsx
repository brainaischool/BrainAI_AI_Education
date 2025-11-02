import React from 'react';
import SectionTitle from './SectionTitle';
import CheckIcon from './CheckIcon';
import SkillCard from './SkillCard';

export default function StudentExchange() {
    const collaborationProcess = [
        { icon: '🤝', title: '팀 빌딩 및 주제 선정', description: '양국 학생들이 혼합 팀을 구성하고, 공동으로 해결할 글로벌 사회 문제(예: 환경, 보건)를 주제로 선정합니다.' },
        { icon: '📝', title: '아이디어 구체화 및 계획', description: '온/오프라인으로 소통하며 아이디어를 구체화하고, 역할 분담 및 프로젝트 계획을 수립합니다.' },
        { icon: '💻', title: '원격 협업 개발', description: '각자의 국가에서 원격으로 협업하며 AI 모델 개발, 데이터 수집 등 역할을 수행합니다.' },
        { icon: '🌏', title: '문화 교류', description: '프로젝트 외 시간을 활용해 서로의 문화를 이해하고 배우는 활동에 참여합니다.' },
        { icon: '🧩', title: '결과물 통합 및 리허설', description: '양국 학생들이 한자리에 모여 각자 개발한 부분을 통합하고 최종 발표를 준비합니다.' },
        { icon: '🏆', title: '최종 결과 발표', description: '글로벌 청중 앞에서 공동의 프로젝트 결과물을 발표하고 성과를 공유합니다.' },
    ];
    
    const outcomes = [
        {
            title: "글로벌 협업 및 커뮤니케이션 능력",
            description: "다양한 문화적 배경을 가진 싱가포르 학생들과 공동의 AI 프로젝트를 수행하며, 글로벌 환경에서의 소통과 협업 능력을 극대화합니다."
        },
        {
            title: "국제적 AI 기술 동향 및 시야 확장",
            description: "양국 학생들이 각자의 아이디어와 기술적 접근법을 공유하며, AI 분야에 대한 국제적 시야와 폭넓은 이해를 갖추게 됩니다."
        },
        {
            title: "문화적 감수성 및 글로벌 리더십 함양",
            description: "단순한 기술 교류를 넘어, 문화 교류 활동을 통해 상호 존중과 이해를 바탕으로 한 글로벌 리더십의 기초를 다집니다."
        }
    ];

    const wefSkills = [
        {
            title: 'Analytical Thinking',
            koreanTitle: '분석적 사고',
            description: '양국 학생들이 공동으로 선정한 글로벌 사회 문제를 데이터 기반으로 분석하고, AI를 활용한 해결 방안의 타당성을 논리적으로 검토하며 프로젝트를 설계합니다.'
        },
        {
            title: 'Motivation and Self-awareness',
            koreanTitle: '동기부여 및 자기 인식',
            description: '글로벌 협업 과정에서 발생하는 성공과 실패를 통해 스스로의 역할과 강점을 성찰하고, 문화적 차이를 이해하며 능동적으로 소통하고 학습합니다.'
        },
        {
            title: 'Resilience, Flexibility, and Agility',
            koreanTitle: '회복탄력성, 유연성, 민첩성',
            description: '서로 다른 작업 방식과 시차, 언어의 장벽 속에서 발생하는 갈등과 어려움을 유연하게 대처하며, 글로벌 협업 환경에 민첩하게 적응합니다.'
        },
        {
            title: 'Leadership and Social Influence',
            koreanTitle: '리더십과 사회적 영향력',
            description: '다양한 문화적 배경을 가진 팀원들의 의견을 조율하고 공동의 목표를 설정하며, 긍정적인 영향력을 통해 팀의 시너지를 극대화합니다.'
        }
    ];


    return (
        <section id="student-exchange" className="py-24 animate-fade-in-up" style={{ animationDelay: '700ms' }}>
            <SectionTitle number="06" title="South Korea & Singapore Student Exchange" />
            
            <div className="mb-20">
                <h4 className="text-2xl font-bold text-brain-lightest-slate text-center mb-10">글로벌 교류와 WEF 미래 핵심역량의 만남</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {wefSkills.map(skill => (
                        <SkillCard key={skill.title} skill={skill} />
                    ))}
                </div>
            </div>

            <div className="mb-20">
                <h4 className="text-2xl font-bold text-brain-lightest-slate text-center mb-10">글로벌 AI 프로젝트 협업 프로세스</h4>
                 <div className="relative max-w-4xl mx-auto mt-10">
                    <div className="hidden lg:block absolute top-1/2 left-0 w-full h-0.5 bg-brain-light-navy -translate-y-1/2"></div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {collaborationProcess.map((step, index) => (
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
                 <p className="text-center text-lg text-brain-light-slate mb-12">BrainAI는 국경을 넘어 AI로 소통하고 협력하는 미래의 글로벌 리더를 양성합니다.</p>
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
                     <p className="font-bold text-brain-lightest-slate">최종 결과물: 양국 학생 공동의 AI 프로젝트 결과물 및 글로벌 캠프 참가 인증서</p>
                 </div>
            </div>

        </section>
    );
};