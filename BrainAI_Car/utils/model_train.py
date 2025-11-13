"""
BrainAI Car 자율주행 도로 인식 모델 훈련 (MobileNet 버전)_v1.0.0
utils/model_model.py

이 모듈은:
1. dataset_laneD1 폴더의 train/validation 데이터를 읽어서
2. MobileNet 기반 Transfer Learning으로 CNN 모델을 훈련시킵니다

[주요 특징]
- MobileNet Transfer Learning 사용
- 빠른 학습 속도
- 적은 데이터로도 높은 성능
- 교육용 상세 주석

[학습 목표]
- Transfer Learning이 무엇인지 이해하기
- MobileNet 구조 이해하기
- 실무에서 사용하는 효율적인 AI 개발 방법 배우기
"""

import os
import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import cv2
import matplotlib.pyplot as plt
from datetime import datetime
import platform


# ============================================================================
# 🎓 1단계: 설정 클래스 (Configuration)
# ============================================================================

class TrainingConfig:
    """
    훈련 설정을 담는 클래스
    
    [중요 개념]
    - 설정을 한 곳에 모아두면 나중에 수정하기 쉬워요!
    - 각 값의 의미를 이해하는 것이 중요합니다
    
    [새로운 기능 - A에서 가져옴]
    - use_augmentation: 데이터 증강 사용 여부
    - augmentation_options: 증강 옵션 선택
    """
    
    def __init__(
        self,
        dataset_laneD1_path="dataset_laneD1",      # 데이터셋 경로
        model_name="brainai_car",    # 모델 이름
        epochs=50,                   # 훈련 반복 횟수
        batch_size=32,               # 한번에 처리할 이미지 수
        img_height=224,              # 이미지 높이
        img_width=224,               # 이미지 너비
        learning_rate=0.001,         # 학습 속도
        use_augmentation=False,      # 데이터 증강 사용
        augmentation_options=None    # 증강 옵션
    ):
        
        self.dataset_laneD1_path = dataset_laneD1_path
        self.model_name = model_name
        self.epochs = epochs
        self.batch_size = batch_size
        self.img_height = img_height
        self.img_width = img_width
        self.learning_rate = learning_rate
        self.use_augmentation = use_augmentation
        self.augmentation_options = augmentation_options or {
            'COLOR_JITTER': False,      # ✅ 색상/밝기 변화 (안전)
            'GAUSSIAN_NOISE': False     # ✅ 노이즈 추가 (안전)
        }
        
    def print_summary(self):
        """설정 요약 출력"""
        print("\n" + "=" * 60)
        print("📋 훈련 설정")
        print("=" * 60)
        print(f"📂 데이터셋: {self.dataset_laneD1_path}")
        print(f"🏷️  모델명: {self.model_name}")
        print(f"🔁 에포크(반복): {self.epochs}회")
        print(f"📦 배치 크기: {self.batch_size}개")
        print(f"🖼️  이미지 크기: {self.img_width}x{self.img_height}")
        print(f"⚡ 학습률: {self.learning_rate}")
        print(f"🎨 데이터 증강: {'사용' if self.use_augmentation else '미사용'}")
        
        if self.use_augmentation:
            print("\n  📊 증강 옵션 (자율주행 안전 증강만):")
            
            # 안전한 옵션
            safe_options = []
            if self.augmentation_options.get('COLOR_JITTER', False):
                safe_options.append("Color Jitter (색상/밝기 변화)")
            if self.augmentation_options.get('GAUSSIAN_NOISE', False):
                safe_options.append("Gaussian Noise (노이즈 추가)")
            
            if safe_options:
                print("    ✅ 안전한 증강:")
                for opt in safe_options:
                    print(f"       - {opt}")
            else:
                print("    (선택된 안전한 증강 없음)")
        
        print("=" * 60)


# ============================================================================
# 🎓 2단계: 데이터 처리 클래스 (Data Utilities)
# ============================================================================

class DataLoader:
    """
    데이터를 불러오고 전처리하는 클래스
    
    [중요 개념]
    - 이미지를 컴퓨터가 이해할 수 있는 숫자로 변환해요
    - 정규화(Normalization): 값을 일정 범위로 조정하여 학습을 쉽게 만들어요
    
    [MobileNet 전처리 특징]
    - 정규화 범위: -1 ~ 1 (MobileNet 표준)
    - 상단 마스킹: 하늘/배경 부분 제거
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        
        # 경로 설정
        self.train_images_path = os.path.join(config.dataset_laneD1_path, "train", "images")
        self.train_annotations_path = os.path.join(config.dataset_laneD1_path, "train", "annotations")
        self.val_images_path = os.path.join(config.dataset_laneD1_path, "validation", "images")
        self.val_annotations_path = os.path.join(config.dataset_laneD1_path, "validation", "annotations")
    
    def apply_augmentation(self, img):
        """
        데이터 증강 적용
        
        [자율주행 데이터 증강 원칙] ⚠️ 매우 중요!
        
        ✅ 안전한 증강 (Pixel-level):
        - 밝기, 대비, 색상 변화
        - 노이즈 추가
        - 블러 효과
        → 도로의 "위치"는 그대로, "보이는 방식"만 변경
        → 조향값 변경 불필요
        
        ❌ 위험한 증강 (Spatial):
        - 좌우/상하 반전
        - 회전, 이동
        - 원근 변환
        → 도로의 "위치"가 변경됨
        → 조향값도 함께 변경해야 하는데 여기서는 불가능
        
        [예시로 이해하기]
        상황: 왼쪽으로 꺾는 도로 (조향값 30도)
        
        ✅ 밝기 변경: 어두운 왼쪽 도로
        → 여전히 왼쪽이므로 조향값 30도 유지 (OK!)
        
        ❌ 좌우 반전: 오른쪽으로 꺾는 도로
        → 오른쪽인데 조향값은 30도(왼쪽) (위험!)
        → 조향값을 70도(오른쪽)로 바꿔야 하는데
            이 함수에서는 이미지만 처리하므로 불가능
        """
        if not self.config.use_augmentation:
            return img
        
        # ✅ Color Jitter (색상 변화) - 안전함
        if self.config.augmentation_options.get('COLOR_JITTER', False):
            if np.random.random() > 0.5:
                # 밝기 조정 (0.8~1.2배)
                brightness_factor = np.random.uniform(0.8, 1.2)
                img = np.clip(img * brightness_factor, 0, 1)
                
                # 대비 조정 (0.8~1.2배)
                if np.random.random() > 0.5:
                    contrast_factor = np.random.uniform(0.8, 1.2)
                    mean = np.mean(img)
                    img = np.clip((img - mean) * contrast_factor + mean, 0, 1)
        
        # ✅ Gaussian Noise (가우시안 노이즈) - 안전함
        if self.config.augmentation_options.get('GAUSSIAN_NOISE', False):
            if np.random.random() > 0.5:
                # 센서 노이즈 시뮬레이션
                noise = np.random.normal(0, 0.05, img.shape)
                img = np.clip(img + noise, 0, 1)
        
        return img
    
    def load_image_and_label(self, img_path, json_path):
        """
        이미지와 라벨(조향값) 한 쌍을 불러오기
        
        [MobileNet 전처리 과정]
        1. 이미지 파일 읽기
        2. 크기 조정 (모든 이미지를 같은 크기로)
        3. 색상 변환 (BGR → RGB)
        4. 정규화 (0~255 → 0~1)
        5. 데이터 증강 적용 (선택사항)
        6. 상단 마스킹 (하늘 부분 제거)
        7. MobileNet 정규화 (0~1 → -1~1)
        8. JSON에서 조향값 읽기 (-1~1 범위)
        """
        # 1. 이미지 읽기
        img = cv2.imread(img_path)
        if img is None:
            print(f"  ⚠️ 이미지 로드 실패: {os.path.basename(img_path)}")
            return None, None
        
        # 2. 크기 조정
        img = cv2.resize(img, (self.config.img_width, self.config.img_height))
        
        # 3. BGR → RGB 변환
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 4. 정규화: 0~255 → 0~1
        img = img.astype(np.float32) / 255.0
        
        # 5. 데이터 증강 적용
        img = self.apply_augmentation(img)
               
        # 6. MobileNet 전처리: 0~1 → -1~1
        img = img * 2.0 - 1.0
        
        # 7. JSON 읽기 및 검증
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 'steering' 키 확인
                if 'steering' not in data:
                    print(f"  ⚠️ 'steering' 키가 없음: {os.path.basename(json_path)}")
                    return None, None
                
                steering = data['steering']
                
                # 조향값 타입 검증
                if not isinstance(steering, (int, float)):
                    print(f"  ⚠️ 잘못된 조향값 타입: {os.path.basename(json_path)}")
                    return None, None
                
                # 조향값 범위 검증 및 클리핑
                if not (-1.0 <= steering <= 1.0):
                    print(f"  ⚠️ 조향값 범위 초과 ({steering}): {os.path.basename(json_path)}")
                    steering = max(-1.0, min(1.0, steering))

                return img, steering
                
        except json.JSONDecodeError:
            print(f"  ⚠️ JSON 파싱 실패: {os.path.basename(json_path)}")
            return None, None
        except FileNotFoundError:
            print(f"  ⚠️ JSON 파일 없음: {os.path.basename(json_path)}")
            return None, None
        except Exception as e:
            print(f"  ⚠️ 예상치 못한 오류: {os.path.basename(json_path)} - {e}")
            return None, None
    
    def load_dataset_laneD1(self, images_dir, annotations_dir):
        """전체 데이터셋 불러오기 (검증 강화)"""
        images = []
        labels = []
        failed_files = []
        
        if not os.path.exists(images_dir):
            print(f"⚠️ 경로가 존재하지 않습니다: {images_dir}")
            return np.array([]), np.array([])
        
        # 이미지 파일 목록 가져오기
        image_files = sorted([f for f in os.listdir(images_dir) if f.endswith('.jpg')])
        total_files = len(image_files)
        
        if total_files == 0:
            print(f"⚠️ 이미지 파일이 없습니다: {images_dir}")
            return np.array([]), np.array([])
        
        print(f"📂 {total_files}개 이미지 발견...")
        
        loaded_count = 0
        for idx, img_file in enumerate(image_files, 1):
            # 이미지 경로
            img_path = os.path.join(images_dir, img_file)
            
            # JSON 경로
            base_name = os.path.splitext(img_file)[0]
            json_path = os.path.join(annotations_dir, f"{base_name}.json")
            
            # 이미지와 라벨 로드
            img, label = self.load_image_and_label(img_path, json_path)
            
            if img is not None and label is not None:
                images.append(img)
                labels.append(label)
                loaded_count += 1
            else:
                failed_files.append(img_file)
                            
            # 10%마다 표시
            if idx % max(1, total_files // 10) == 0:
                progress = (idx / total_files) * 100
                print(f"⏳ 진행중... {progress:.0f}%")
        
        print(f"\n  ✅ {loaded_count}개 로드 완료! (100.0%)              ")
        
        # 로드 성공률 계산
        success_rate = (loaded_count / total_files * 100) if total_files > 0 else 0
        
        # 실패 파일 상세 정보
        if failed_files:
            print(f"\n  ⚠️ {len(failed_files)}개 파일 로드 실패 (실패율: {100-success_rate:.1f}%)")
            if len(failed_files) <= 10:
                print(f"     실패한 파일 목록:")
                for f in failed_files:
                    print(f"       - {f}")
            else:
                print(f"     실패한 파일 예시 (처음 10개):")
                for f in failed_files[:10]:
                    print(f"       - {f}")
                print(f"     ... 외 {len(failed_files)-10}개")
        
        # 🔴 심각한 문제: 로드 성공률이 너무 낮음
        if success_rate < 50:
            print(f"\n  🔴 심각한 오류: 로드 성공률 {success_rate:.1f}%")
            print(f"     전체 {total_files}개 중 {loaded_count}개만 로드됨")
            print(f"\n  💡 가능한 원인:")
            print(f"     1. JSON 파일이 없거나 손상됨")
            print(f"     2. 이미지 파일이 손상됨")
            print(f"     3. 'steering' 키가 없거나 값이 잘못됨")
            print(f"     4. 파일명이 일치하지 않음 (예: image_001.jpg ↔ image_001.json)")
            print(f"\n  ❌ 데이터를 다시 확인하세요!")
            raise ValueError(f"데이터 로드 실패율이 너무 높습니다 ({100-success_rate:.1f}%)")
        
        # 🟡 주의: 로드 성공률이 낮음
        elif success_rate < 80:
            print(f"\n  ⚠️ 주의: 로드 성공률 {success_rate:.1f}%")
            print(f"     전체 {total_files}개 중 {loaded_count}개 로드됨")
            print(f"     {len(failed_files)}개 파일에 문제가 있습니다")
            print(f"\n  💡 권장사항:")
            print(f"     - 실패한 파일들을 확인하여 수정하세요")
            print(f"     - 80% 미만의 성공률은 모델 성능에 영향을 줄 수 있습니다")
        
        # ✅ 정상: 로드 성공률이 높음
        elif success_rate >= 80:
            print(f"\n  ✅ 로드 성공률: {success_rate:.1f}%")
            if failed_files:
                print(f"     ({len(failed_files)}개 파일 제외됨)")
        
        # 🔴 절대 데이터 수 검증 (새로운 기준)
        print(f"\n  📊 데이터 품질 평가:")
        if loaded_count < 100:
            print(f"     🔴 매우 부족: {loaded_count}개")
            print(f"        → 최소 100개 필요, 학습 실패 가능성 높음")
            raise ValueError(f"데이터가 너무 적습니다 ({loaded_count}개). 최소 100개 필요!")
        elif loaded_count < 300:
            print(f"     🟡 부족: {loaded_count}개")
            print(f"        → 기본 학습 가능하나 500개 이상 권장")
        elif loaded_count < 500:
            print(f"     🟢 보통: {loaded_count}개")
            print(f"        → 기본 학습 가능")
        elif loaded_count < 1000:
            print(f"     🟢 양호: {loaded_count}개")
            print(f"        → 좋은 학습 성능 기대")
        else:
            print(f"     🌟 우수: {loaded_count}개")
            print(f"        → 매우 좋은 학습 성능 기대")
        
        return np.array(images), np.array(labels)

    def load_all_data(self):
        """훈련 및 검증 데이터 모두 로드"""
        print("\n" + "=" * 60)
        print("📥 데이터 로드 중...")
        print("=" * 60)
        
        # 훈련 데이터
        print("\n[훈련 데이터]")
        train_images, train_labels = self.load_dataset_laneD1(
            self.train_images_path,
            self.train_annotations_path
        )
        
        # 검증 데이터
        print("\n[검증 데이터]")
        val_images, val_labels = self.load_dataset_laneD1(
            self.val_images_path,
            self.val_annotations_path
        )
        
        if len(train_images) == 0:
            raise ValueError("❌ 훈련 데이터가 없습니다!")
        
        # 🆕 전체 요약 추가
        total_data = len(train_images) + len(val_images)
        
        print(f"\n" + "=" * 60)
        print(f"✅ 전체 데이터 로드 완료")
        print("=" * 60)
        print(f"  📊 훈련 데이터: {len(train_images):,}개")
        print(f"  📊 검증 데이터: {len(val_images):,}개")
        print(f"  📊 전체 합계: {total_data:,}개")
        print(f"  📊 훈련/검증 비율: {len(train_images)/total_data*100:.1f}% / {len(val_images)/total_data*100:.1f}%")
        
        # 데이터셋 균형 확인
        if len(val_images) == 0:
            print(f"\n  ⚠️ 경고: 검증 데이터가 없습니다!")
            print(f"     모델 성능 평가가 불가능합니다")
        elif len(val_images) / total_data < 0.1:
            print(f"\n  ⚠️ 주의: 검증 데이터 비율이 낮습니다 ({len(val_images)/total_data*100:.1f}%)")
            print(f"     일반적으로 10-20% 권장")
        elif len(val_images) / total_data > 0.3:
            print(f"\n  ⚠️ 주의: 검증 데이터 비율이 높습니다 ({len(val_images)/total_data*100:.1f}%)")
            print(f"     훈련 데이터가 부족할 수 있습니다")
        
        print("=" * 60)
        
        return train_images, train_labels, val_images, val_labels

# ============================================================================
# 🎓 3단계: MobileNet 모델 구축 (Model Builder)
# ============================================================================

class ModelBuilder:
    """
    MobileNet 기반 CNN 모델을 만드는 클래스
    
    [Transfer Learning이란?]
    - 이미 다른 작업으로 학습된 모델을 가져와서 사용
    - MobileNet은 ImageNet(1,400만 장)으로 이미 학습됨
    - 선, 곡선, 경계선 등 기본 특징을 이미 알고 있음
    - 우리는 "조향 예측"만 새로 학습하면 됨!
    
    [왜 MobileNet인가?]
    - ✅ 경량화된 모델 (모바일에서도 작동)
    - ✅ 빠른 추론 속도
    - ✅ 적은 파라미터
    - ✅ 검증된 성능
    
    [모델 구조]
    1. MobileNetV3Large (고정): 특징 추출
    2. GlobalAveragePooling2D: 특징 압축
    3. Dense 레이어들: 조향 각도 예측
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
    
    def build_mobilenet_model(self):
        """
        MobileNet 기반 모델 구축
        
        [구조 설명]
        
        🔒 고정 부분 (MobileNet):
        - ImageNet으로 사전 학습됨
        - 이미지에서 특징 추출
        - 학습하지 않음 (trainable=False)
        
        🆕 새로 학습할 부분:
        - GlobalAveragePooling2D: 특징 요약
        - Dense(64): 중간 의사결정
        - Dense(32): 세부 의사결정
        - Dense(1): 최종 조향 각도 출력
        
        [출력]
        - 최종 조향 출력: -1 ~ 1
        """
        print("\n" + "=" * 60)
        print("🏗️ MobileNet 기반 모델 구축 중...")
        print("=" * 60)
        
        print("\n💡 Transfer Learning 적용:")
        print("  - 사전학습 데이터: ImageNet (1,400만 장)")
        print("  - 사전학습 카테고리: 1,000개 (동물, 차량, 사물 등)")
        print("  - 고정 부분: 특징 추출 레이어 (MobileNet)")
        print("  - 학습 부분: 조향 예측 레이어 (Dense)")
        print("\n🎯 장점:")
        print("  - 빠른 학습 (50 에포크면 충분)")
        print("  - 적은 데이터로 높은 성능")
        print("  - 안정적인 학습")
        
        # ===== 1. MobileNet 기본 모델 가져오기 =====
        print("\n📦 MobileNetV3Large 로드 중...")
        
        base_model = keras.applications.MobileNetV3Large(
            input_shape=(self.config.img_height, self.config.img_width, 3),
            include_top=False,   # 분류층 제외 (우리가 직접 만들 것)
            weights='imagenet',  # 사전 학습된 가중치 사용
            minimalistic=False,  # 표준 구조 사용
            alpha=0.75          # 모델 크기 (0.75 = 25% 경량화)
        )
        
        # ===== 2. 기존 학습 내용 보존 =====
        # MobileNet이 배운 것을 그대로 유지
        base_model.trainable = False
        
        print(f"  ✅ MobileNet 로드 완료")
        print(f"  📊 총 레이어: {len(base_model.layers)}개")
        print(f"  🔒 고정 상태: trainable=False")
        
        # ===== 3. 조향 예측 레이어 추가 =====
        print("\n🔧 조향 예측 레이어 추가 중...")
        
        model = keras.Sequential([
            # 🔒 고정된 특징 추출 (MobileNet)
            base_model,
            
            # 특징 압축
            layers.GlobalAveragePooling2D(),
            
            # 🆕 새로 학습할 의사결정 레이어들
            layers.Dense(64, activation='relu', name='steering_fc1'),
            layers.Dropout(0.2, name='dropout1'),
            
            layers.Dense(32, activation='relu', name='steering_fc2'),
            
            # 최종 조향 출력: -1 ~ 1
            layers.Dense(1, activation='tanh', name='steering_output')
        ], name='BrainAI_Car_MobileNet')
        
        # ===== 4. 모델 컴파일 =====
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.config.learning_rate),
            loss='mse',      # Mean Squared Error
            metrics=['mae']  # Mean Absolute Error
        )
        
        print("  ✅ 조향 예측 레이어 추가 완료")
        
        # ===== 5. 모델 정보 출력 =====
        print("\n" + "=" * 60)
        print("✅ 모델 구축 완료!")
        print("=" * 60)
        
        # 파라미터 통계
        total_params = model.count_params()
        trainable_params = sum([tf.size(w).numpy() for w in model.trainable_weights])
        non_trainable_params = total_params - trainable_params
        
        print(f"\n📊 모델 통계:")
        print(f"  - 전체 파라미터: {total_params:,}개")
        print(f"  - 학습 파라미터: {trainable_params:,}개 (조향 예측)")
        print(f"  - 고정 파라미터: {non_trainable_params:,}개 (MobileNet)")
        print(f"  - 학습 비율: {trainable_params/total_params*100:.1f}%")
        
        print("\n📋 모델 구조:")
        model.summary()
        
        return model


# ============================================================================
# 🎓 4단계: 모델 훈련기 (Trainer)
# ============================================================================

class ModelTrainer:
    """
    모델을 훈련시키는 클래스
    
    [훈련 과정]
    1. 데이터를 모델에 보여주기
    2. 모델이 예측하기
    3. 예측이 얼마나 틀렸는지 계산 (Loss)
    4. 틀린 만큼 모델 조정하기
    5. 1~4를 반복!
    
    [MobileNet 훈련 특징]
    - 빠른 수렴: 50 에포크면 충분
    - 안정적: 사전 학습으로 초기 성능 높음
    - 조기 종료: 개선 없으면 자동 중단
    """
    
    def __init__(self, config: TrainingConfig, models_dir="models"):
        self.config = config
        self.model = None
        self.history = None
        
        # 모델 저장 폴더
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
    
    def setup_callbacks(self):
        """
        콜백 설정
        
        [콜백이란?]
        - 훈련 중 자동으로 실행되는 기능들
        
        [MobileNet 최적화 콜백]
        1. ModelCheckpoint: 최고 성능 모델 저장
        2. EarlyStopping: patience=5 (적당한 인내)
        3. ReduceLROnPlateau: 학습률 자동 감소
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(
            self.models_dir,
            f"{self.config.model_name}_mobilenet_{timestamp}.keras"
        )
        
        callbacks = [
            # 📌 최고 성능 모델 저장
            keras.callbacks.ModelCheckpoint(
                filepath=model_path,
                monitor='val_loss',
                save_best_only=True,
                verbose=1
            ),
            
            # 🛑 조기 종료 (5 에포크 동안 개선 없으면)
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True,
                verbose=1
            ),
            
            # 📉 학습률 감소
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            )
        ]
        
        print(f"\n💾 모델 저장 경로: {model_path}")
        
        return callbacks
    
    def train(self, model, train_images, train_labels, val_images, val_labels):
        """
        모델 훈련 실행
        
        [화면 읽는 법]
        - Epoch: 현재 반복 횟수
        - loss: 훈련 오차 (낮을수록 좋음)
        - mae: 평균 절대 오차 (예측이 평균 몇 도 틀렸는지)
        - val_loss: 검증 오차
        - val_mae: 검증 평균 절대 오차
        
        [좋은 학습의 신호]
        ✅ loss와 val_loss가 비슷하게 감소
        ✅ mae가 2도 이하로 수렴
        ❌ val_loss가 증가 → 과적합!
        """
        print("\n" + "=" * 60)
        print(f"🚀 MobileNet 모델 훈련 시작 - {self.config.epochs} 에포크")
        print("=" * 60)
        print("\n💡 Tip:")
        print("  - MobileNet은 빠르게 수렴합니다")
        print("  - 보통 20~50 에포크면 충분합니다")
        print("  - val_loss가 더 이상 감소하지 않으면 자동 중단됩니다")
        print("=" * 60)
        
        callbacks = self.setup_callbacks()
        
        # 훈련 시작!
        self.history = model.fit(
            train_images,
            train_labels,
            batch_size=self.config.batch_size,
            epochs=self.config.epochs,
            validation_data=(val_images, val_labels),
            callbacks=callbacks,
            verbose=1
        )
        
        self.model = model
        
        print("\n✅ 훈련 완료!")
        
        return self.history
    
    def evaluate(self, val_images, val_labels):
        """모델 성능 평가"""
        print("\n" + "=" * 60)
        print("📊 MobileNet 모델 평가")
        print("=" * 60)
        
        loss, mae = self.model.evaluate(val_images, val_labels, verbose=0)
                
        print(f"\n검증 데이터 성능:")
        print(f"  📉 Loss (MSE): {loss:.4f}")
        print(f"  📏 MAE: {mae:.4f}")
        
        # 성능 평가 (조향값 범위: -1~1, MAE 0.04 ≈ 실제 2도 오차)
        if mae < 0.04:
            print(f"\n  🎉 우수한 성능입니다! (MAE < 0.04)")
        elif mae < 0.07:
            print(f"\n  ✅ 좋은 성능입니다! (MAE < 0.07)")
        elif mae < 0.10:
            print(f"\n  ⚠️ 개선 여지가 있습니다. (MAE < 0.10)")
        else:
            print(f"\n  ❌ 데이터나 설정을 점검해보세요.")
            
        # 예측 샘플
        print(f"\n🎯 예측 샘플 (5개):")
        predictions = self.model.predict(val_images[:5], verbose=0)
        
        for i in range(5):
            actual = val_labels[i]
            predicted = predictions[i][0]
            error = abs(actual - predicted)
            
            print(f"  {i+1}. 실제: {actual:6.3f} | "
                f"예측: {predicted:6.3f} | "
                f"오차: {error:5.3f}")  
    
    def _setup_korean_font(self):
        """한글 폰트 설정 (시스템별 대응)"""
        system = platform.system()
        
        try:
            if system == 'Windows':
                plt.rcParams['font.family'] = 'Malgun Gothic'
            elif system == 'Darwin':  # macOS
                plt.rcParams['font.family'] = 'AppleGothic'
            else:  # Linux
                plt.rcParams['font.family'] = 'NanumGothic'
            
            # 마이너스 기호 깨짐 방지
            plt.rcParams['axes.unicode_minus'] = False
            
        except Exception as e:
            print("⚠️ 한글 폰트를 찾을 수 없습니다. 영문으로 표시됩니다.")
    
    def plot_history(self):
        """훈련 과정 그래프 그리기"""
        if self.history is None:
            print("⚠️ 훈련 기록이 없습니다!")
            return
        
        # 한글 폰트 설정
        self._setup_korean_font()
        
        plt.figure(figsize=(12, 4))
           
        # Loss 그래프
        plt.subplot(1, 2, 1)
        plt.plot(self.history.history['loss'], label='훈련 Loss', linewidth=2)
        plt.plot(self.history.history['val_loss'], label='검증 Loss', linewidth=2)
        plt.title('MobileNet 모델 Loss', fontsize=14, fontweight='bold')
        plt.xlabel('에포크', fontsize=12)
        plt.ylabel('Loss', fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        
        # MAE 그래프
        plt.subplot(1, 2, 2)
        plt.plot(self.history.history['mae'], label='훈련 MAE', linewidth=2)
        plt.plot(self.history.history['val_mae'], label='검증 MAE', linewidth=2)
        plt.title('평균 절대 오차 (MAE)', fontsize=14, fontweight='bold')
        plt.xlabel('에포크', fontsize=12)
        plt.ylabel('MAE', fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 저장
        plot_path = os.path.join(
            self.models_dir,
            f"{self.config.model_name}_mobilenet_history.png"
        )
        plt.savefig(plot_path, dpi=150)
        print(f"\n📊 훈련 그래프 저장: {plot_path}")
        
        plt.show()
    
    def save_final_model(self):
        """최종 모델 저장"""
        if self.model is None:
            print("⚠️ 저장할 모델이 없습니다!")
            return
        
        save_path = os.path.join(
            self.models_dir,
            f"{self.config.model_name}_mobilenet_final.keras"
        )
        self.model.save(save_path)
        print(f"\n💾 최종 모델 저장: {save_path}")


# ============================================================================
# 🎓 5단계: 통합 훈련 함수
# ============================================================================

def model_train(config: TrainingConfig, models_dir="models"):
    """
    전체 훈련 과정 실행 함수
    
    [MobileNet Transfer Learning 전체 흐름]
    1. 설정 출력
    2. 데이터 로드 (MobileNet 전처리)
    3. MobileNet 모델 구축
    4. 모델 훈련
    5. 성능 평가
    6. 결과 저장
    
    [왜 MobileNet인가?]
    - ⚡ 빠른 학습: Custom CNN 대비 50% 시간 절약
    - 🎯 높은 성능: 적은 데이터로도 우수한 결과
    - 💪 안정적: 사전 학습으로 안정적인 수렴
    - 🌍 실무 표준: 업계에서 널리 사용
    
    Args:
        config: 훈련 설정
        models_dir: 모델 저장 폴더
    """
    # GPU 메모리 최적화 설정
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            print(f"✅ GPU {len(gpus)}개 발견 - 메모리 증가 제한 활성화")
        except RuntimeError as e:
            print(f"⚠️ GPU 설정 실패: {e}")
    else:
        print("ℹ️ GPU 없음 - CPU로 훈련 (시간이 오래 걸릴 수 있습니다)")
    
    # Transfer Learning 안내
    print("\n" + "=" * 60)
    print("🎓 Transfer Learning with MobileNet")
    print("=" * 60)
    print("\n[Transfer Learning이란?]")
    print("  이미 다른 작업으로 학습된 모델을 활용하는 기법")
    print("\n[MobileNet 사전 학습 정보]")
    print("  - 데이터: ImageNet (1,400만 장)")
    print("  - 카테고리: 1,000개 (동물, 차량, 사물 등)")
    print("  - 학습 내용: 선, 곡선, 경계, 질감, 패턴 등")
    print("\n[우리가 할 일]")
    print("  - MobileNet: 특징 추출 (이미 학습됨, 고정)")
    print("  - Dense 레이어: 조향 예측 (새로 학습)")
    print("\n[장점]")
    print("  ⚡ 빠른 학습 속도 (50 에포크면 충분)")
    print("  🎯 높은 초기 성능 (첫 에포크부터 좋은 결과)")
    print("  💾 적은 데이터 필요 (500~1,000장으로도 가능)")
    
    config.print_summary()
    
    try:
        # 1️⃣ 데이터 로더 생성 및 데이터 로드
        data_loader = DataLoader(config)
        train_images, train_labels, val_images, val_labels = data_loader.load_all_data()
        
        # 2️⃣ MobileNet 모델 구축
        model_builder = ModelBuilder(config)
        model = model_builder.build_mobilenet_model()
        
        # 3️⃣ 트레이너로 모델 훈련
        trainer = ModelTrainer(config, models_dir)
        trainer.train(model, train_images, train_labels, val_images, val_labels)
        
        # 4️⃣ 성능 평가
        trainer.evaluate(val_images, val_labels)
        
        # 5️⃣ 최종 모델 저장
        trainer.save_final_model()
        
        # 6️⃣ 훈련 그래프 생성
        trainer.plot_history()
        
        # 완료 메시지
        print("\n" + "=" * 60)
        print("✅ MobileNet 훈련 완료!")
        print("=" * 60)
        print("\n📁 생성된 파일:")
        print("  • models/ 폴더에 훈련된 MobileNet 모델")
        print("  • 훈련 그래프 이미지")
        print("\n🎯 다음 단계:")
        print("  1. 자율주행 테스트 실행")
        print("  2. 성능이 부족하면 Fine-tuning 실행")
        print("  3. 더 많은 데이터 수집 후 모델 업데이트")
        print("\n💡 Fine-tuning이란?")
        print("  - MobileNet의 일부 레이어 일부를 학습 가능 상태로 전환하여 추가로 미세 조정하는 과정")
        print("  - 도로 인식에 더 특화되게 최적화")
        print("  - update_model.py 사용")
        
    except ValueError as e:
        print(f"\n❌ 데이터 오류: {e}")
        print("\n💡 해결 방법:")
        print("  1. dataset_laneD1 폴더 구조 확인:")
        print("     dataset_laneD1/")
        print("     ├── train/")
        print("     │   ├── images/")
        print("     │   └── annotations/")
        print("     └── validation/")
        print("         ├── images/")
        print("         └── annotations/")
        print("  2. 이미지와 JSON 파일이 있는지 확인")
        print("  3. MobileNet은 적은 데이터로도 작동하지만")
        print("     최소 500장 이상 권장")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 문제 해결:")
        print("  1. 오류 메시지를 잘 읽어보세요")
        print("  2. 선생님께 오류 메시지를 보여주세요")
        print("  3. TensorFlow가 제대로 설치되었는지 확인")


# 버전 정보
__version__ = '1.0.0'
__author__ = 'BrainAI Co,.Ltd.'
__description__ = 'BrainAI Autonomous Driving Project - MobileNet Transfer Learning Module'