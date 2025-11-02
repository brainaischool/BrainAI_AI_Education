

import React from 'react';
import WEFSkills from './WEFSkills';
import AIProjectCycle from './AIProjectCycle';
import SectionTitle from './SectionTitle';
import CheckIcon from './CheckIcon';

export default function AutonomousCarProject() {
    const outcomes = [
        {
            title: "AI 시대의 핵심 역량 체험 기반 함양",
            description: "지식 습득을 넘어, 자율주행 도전 과정에서 WEF가 강조한 6가지 핵심 역량을 실제로 사용하고 내면화합니다."
        },
        {
            title: "AI 기술의 실제 적용 과정 이해",
            description: "AI 프로젝트 사이클을 완주하며, AI 개발의 '로드맵'과 실무 프로세스를 명확하게 이해하게 됩니다."
        },
        {
            title: "AI + X 융합 아이디어 창출 경험",
            description: "자율주행차를 넘어, AI가 의료, 환경, 산업 등 다양한 분야에 어떻게 융합될 수 있는지에 대한 통찰력과 아이디어를 갖추게 됩니다."
        }
    ];

    return (
        <section id="autonomous-car" className="py-24 animate-fade-in-up" style={{ animationDelay: '600ms' }}>
            <SectionTitle number="05" title="BrainAI Car 자율주행 챌린지" />
            
            <div className="mb-20">
                <h4 className="text-2xl font-bold text-brain-lightest-slate text-center mb-10">BrainAI Car 자율주행 챌린지와 WEF 미래 핵심역량의 만남</h4>
                <WEFSkills />
            </div>

            <div className="mb-20">
                <h4 className="text-2xl font-bold text-brain-lightest-slate text-center mb-10">AI 전문가처럼 학습하는 6단계, AI 프로젝트 사이클</h4>
                <AIProjectCycle />
            </div>

            <div>
                 <h4 className="text-2xl font-bold text-brain-lightest-slate text-center mb-4">교육 목표 및 기대 효과</h4>
                 <p className="text-center text-lg text-brain-light-slate mb-12">BrainAI는 미래 인재로 성장하는 데 필요한 세 가지 핵심 아웃풋을 보장합니다.</p>
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
                     <p className="font-bold text-brain-lightest-slate">최종 결과물: AI 모델과 주행 전략을 담은 개인/팀 포트폴리오 확보</p>
                 </div>
            </div>

        </section>
    );
};