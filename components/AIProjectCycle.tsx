
import React from 'react';

interface CycleStep {
  icon: string;
  title: string;
  description: string;
}

const steps: CycleStep[] = [
  { icon: '🧭', title: '문제 정의', description: '해결하고 싶은 문제는 무엇인가? (예: 특정 코스 완주하기)' },
  { icon: '📊', title: '데이터 획득', description: '주행에 필요한 데이터는 무엇인가? (예: BrainAI Car, 스마트 폰)' },
  { icon: '🔍', title: '데이터 탐색', description: '획득한 데이터를 어떻게 가공하고 전처리할 것인가?' },
  { icon: '🤖', title: '모델링', description: '어떤 AI 알고리즘으로 문제를 해결할 것인가? (예: TensorFlow 모델 설계)' },
  { icon: '✅', title: '모델 평가', description: 'AI 모델 성능이 얼마나 좋은가? 하드웨어에서 최적화되어 있는가? (예: 인텔 PC 사용: OpenVINO로 최적화)' },
  { icon: '🚗', title: '배포', description: '완성된 AI 모델을 자율주행차에 탑재하고 최종 미션을 수행합니다.' },
];

export default function AIProjectCycle() {
  return (
    <div className="relative max-w-4xl mx-auto">
      {/* Connector line for large screens */}
      <div className="hidden lg:block absolute top-1/2 left-0 w-full h-0.5 bg-brain-light-navy -translate-y-1/2"></div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {steps.map((step, index) => (
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
      <p className="text-center mt-12 text-brain-light-slate max-w-2xl mx-auto">
        이 6단계를 직접 경험함으로써, 학생들은 AI 기술이 단순한 이론이 아닌, 실제 문제를 해결하는 강력한 도구임을 깨닫게 됩니다.
      </p>
    </div>
  );
};