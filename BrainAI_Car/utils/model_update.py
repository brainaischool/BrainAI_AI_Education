"""
BrainAI Car 모델 업데이트 (MobileNet Fine-tuning)_v1.0.0
utils/update_model.py

이 모듈은:
1. 기존에 훈련된 MobileNet 모델을 불러와서
2. 새로 수집한 데이터로 Fine-tuning을 합니다
3. MobileNet 일부 레이어를 "해동"하여 도로 인식에 특화

[Fine-tuning이란?]
- MobileNet의 상위 레이어를 학습 가능하게 만들기
- 도로 인식에 더 특화되게 조정
- 기존 학습 내용은 대부분 유지

[언제 사용하나요?]
- 이미 훈련된 MobileNet 모델이 있을 때
- 새로운 코스나 환경에서 데이터를 더 수집했을 때
- 모델 성능을 더욱 향상시키고 싶을 때

[2단계 학습 전략]
1단계: Transfer Learning (train_model.py)
  - MobileNet 고정
  - Dense 레이어만 학습
  - 빠른 학습

2단계: Fine-tuning (이 파일)
  - MobileNet 일부 해동
  - 전체 모델 미세 조정
  - 성능 향상
"""

import os
import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
import cv2
import matplotlib.pyplot as plt
from datetime import datetime


# ============================================================================
# 🎓 1단계: MobileNet Fine-tuner 클래스
# ============================================================================

class MobileNetFineTuner:
    """
    MobileNet 모델을 Fine-tuning하는 클래스
    
    [Fine-tuning 전략]
    1. 기존 모델 로드
    2. MobileNet의 상위 N개 레이어 해동
    3. 매우 낮은 학습률로 학습
    4. 기존 지식 유지하며 도로 인식 특화
    
    [중요!]
    - 학습률을 매우 낮게 설정 (0.00001~0.0001)
    - MobileNet 전체를 해동하면 안 됨 (하위 레이어는 고정)
    - 적은 에포크로 학습 (10~30)
    """
    
    def __init__(self, model_path, new_data_path, models_dir="models"):
        """
        초기화
        
        Args:
            model_path: 기존 MobileNet 모델 파일 경로 (.keras)
            new_data_path: 새로운 데이터셋 경로
            models_dir: 모델 저장 폴더
        """
        self.model_path = model_path
        self.new_data_path = new_data_path
        self.model = None
        self.base_model = None
        self.history = None
        
        # 모델 저장 폴더
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
    
    def load_existing_model(self):
        """
        기존 MobileNet 모델 불러오기
        
        [확인사항]
        - 모델이 MobileNet 기반인지 확인
        - 구조가 올바른지 확인
        """
        print("\n" + "=" * 60)
        print("📂 기존 MobileNet 모델 로드 중...")
        print("=" * 60)
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"❌ 모델을 찾을 수 없습니다: {self.model_path}")
        
        print(f"📁 모델 경로: {self.model_path}")
        
        # 모델 로드
        self.model = keras.models.load_model(self.model_path)
        
        # MobileNet 기본 모델 찾기
        for layer in self.model.layers:
            if isinstance(layer, keras.Model) and 'mobilenet' in layer.name.lower():
                self.base_model = layer
                break
        
        if self.base_model is None:
            print("⚠️ MobileNet 레이어를 찾을 수 없습니다.")
            print("   일반 모델 업데이트로 진행합니다.")
        else:
            print(f"✅ MobileNet 발견: {self.base_model.name}")
            print(f"   총 레이어: {len(self.base_model.layers)}개")
        
        print("\n✅ 모델 로드 완료!")
        print("\n모델 구조:")
        self.model.summary()
        
        return self.model
    
    def unfreeze_top_layers(self, num_layers=20):
        """
        MobileNet 상위 레이어 해동
        
        [Fine-tuning 전략]
        - 하위 레이어: 고정 (일반적인 특징 - 선, 곡선 등)
        - 상위 레이어: 해동 (구체적인 특징 - 도로 패턴 등)
        
        [왜 전체를 해동하지 않나?]
        - 하위 레이어는 이미 충분히 좋은 특징을 학습함
        - 전체 해동 시 과적합 위험
        - 학습 시간 증가
        
        Args:
            num_layers: 해동할 상위 레이어 수 (기본 20개)
        """
        if self.base_model is None:
            print("⚠️ MobileNet을 찾을 수 없어 Fine-tuning을 건너뜁니다.")
            return
        
        print("\n" + "=" * 60)
        print(f"🔓 MobileNet 상위 {num_layers}개 레이어 해동")
        print("=" * 60)
        
        # 전체 MobileNet을 먼저 학습 가능하게
        self.base_model.trainable = True
        
        # 하위 레이어들은 다시 고정
        total_layers = len(self.base_model.layers)
        freeze_until = total_layers - num_layers
        
        for i, layer in enumerate(self.base_model.layers):
            if i < freeze_until:
                layer.trainable = False
            else:
                layer.trainable = True
        
        # 통계 출력
        trainable_count = sum([1 for layer in self.base_model.layers if layer.trainable])
        frozen_count = len(self.base_model.layers) - trainable_count
        
        print(f"\n📊 레이어 상태:")
        print(f"  🔒 고정: {frozen_count}개 (하위 레이어)")
        print(f"  🔓 해동: {trainable_count}개 (상위 레이어)")
        print(f"  📈 해동 비율: {trainable_count/total_layers*100:.1f}%")
        
        print(f"\n💡 Fine-tuning 전략:")
        print(f"  - 하위 레이어 (1~{freeze_until}): 고정")
        print(f"    → 일반적인 특징 유지 (선, 곡선, 경계 등)")
        print(f"  - 상위 레이어 ({freeze_until+1}~{total_layers}): 학습")
        print(f"    → 도로 인식에 특화된 특징 학습")
    
    def load_new_data(self):
        """
        새로운 데이터 불러오기
        
        [MobileNet 전처리]
        - 정규화: -1 ~ 1
        - 상단 마스킹: 적용
        - 크기: 모델 입력 크기와 동일
        """
        print("\n" + "=" * 60)
        print("📥 새로운 데이터 로드 중...")
        print("=" * 60)
        
        # 경로 설정
        train_images_path = os.path.join(self.new_data_path, "train", "images")
        train_annotations_path = os.path.join(self.new_data_path, "train", "annotations")
        val_images_path = os.path.join(self.new_data_path, "validation", "images")
        val_annotations_path = os.path.join(self.new_data_path, "validation", "annotations")
        
        # 훈련 데이터
        print("\n[새 훈련 데이터]")
        train_images, train_labels = self._load_dataset(
            train_images_path,
            train_annotations_path
        )
        
        # 검증 데이터
        print("\n[새 검증 데이터]")
        val_images, val_labels = self._load_dataset(
            val_images_path,
            val_annotations_path
        )
        
        if len(train_images) == 0:
            raise ValueError("❌ 새로운 훈련 데이터가 없습니다!")
        
        print(f"\n✅ 새 데이터 로드 완료:")
        print(f"  - 훈련: {len(train_images)}개")
        print(f"  - 검증: {len(val_images)}개")
        
        return train_images, train_labels, val_images, val_labels
    
    def _load_dataset(self, images_dir, annotations_dir):
        """
        데이터셋 로드 (MobileNet 전처리 적용)
        
        [전처리]
        1. 0~255 → 0~1 정규화
        2. 상단 마스킹 (하늘 제거)
        3. 0~1 → -1~1 (MobileNet 표준)
        """
        images = []
        labels = []
        
        if not os.path.exists(images_dir):
            print(f"⚠️ 경로가 존재하지 않습니다: {images_dir}")
            return np.array([]), np.array([])
        
        # 모델의 입력 크기 가져오기
        img_height, img_width = self.model.input_shape[1:3]
        
        image_files = sorted([f for f in os.listdir(images_dir) if f.endswith('.jpg')])
        total_files = len(image_files)
        
        print(f"📂 {total_files}개 이미지 발견...")
        
        loaded_count = 0
        for idx, img_file in enumerate(image_files, 1):
            img_path = os.path.join(images_dir, img_file)
            base_name = os.path.splitext(img_file)[0]
            json_path = os.path.join(annotations_dir, f"{base_name}.json")
            
            # 이미지 로드
            img = cv2.imread(img_path)
            if img is None:
                continue
            
            img = cv2.resize(img, (img_width, img_height))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = img.astype(np.float32) / 255.0
            
            # 상단 마스킹
            half_height = img_height // 2
            img[:half_height, :, :] = 0
            
            # MobileNet 정규화: -1 ~ 1
            img = img * 2.0 - 1.0
            
            # JSON 로드
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    steering = data['steering']
                    
                    # 범위 체크 및 클리핑                    
                    if not (-1.0 <= steering <= 1.0):
                        steering = max(-1.0, min(1.0, steering))

                    images.append(img)
                    labels.append(steering)
                    loaded_count += 1
                    
                    # 진행상황 표시
                    if idx % 100 == 0 or idx == total_files:
                        progress = (idx / total_files) * 100
                        print(f"  ⏳ 진행중... {idx}/{total_files} ({progress:.1f}%)", end='\r')
            except:
                continue
        
        print(f"\n  ✅ {loaded_count}개 로드 완료!")
        
        return np.array(images), np.array(labels)
    
    def fine_tune(self, train_images, train_labels, val_images, val_labels,
                  epochs=20, learning_rate=0.00005, unfreeze_layers=20):
        """
        MobileNet Fine-tuning 실행
        
        [Fine-tuning 설정]
        - 매우 낮은 학습률: 0.00005 (기존의 1/20)
        - 적은 에포크: 20회
        - 상위 레이어만 해동: 20개
        
        [왜 학습률이 낮은가?]
        - 기존 학습을 망가뜨리지 않기 위해
        - 미세하게 조정만 하는 것이 목표
        - 너무 크면 과적합 위험
        
        Args:
            epochs: Fine-tuning 에포크 수 (기본 20)
            learning_rate: 학습률 (기본 0.00005, 매우 낮음!)
            unfreeze_layers: 해동할 레이어 수 (기본 20)
        """
        print("\n" + "=" * 60)
        print(f"🔧 MobileNet Fine-tuning 시작")
        print("=" * 60)
        
        # 1. 상위 레이어 해동
        self.unfreeze_top_layers(unfreeze_layers)
        
        # 2. 매우 낮은 학습률로 재컴파일
        print(f"\n⚙️ 모델 재컴파일:")
        print(f"  - 학습률: {learning_rate} (매우 낮음!)")
        print(f"  - 손실 함수: MSE")
        print(f"  - 평가 지표: MAE")
        
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        # 3. Fine-tuning 전략 안내
        print(f"\n💡 Fine-tuning 전략:")
        print(f"  - 에포크: {epochs}회 (짧게)")
        print(f"  - 학습률: {learning_rate} (매우 낮게)")
        print(f"  - 목표: 기존 지식 유지 + 도로 특화")
        print("=" * 60)
        
        # 4. 콜백 설정
        callbacks = self._setup_callbacks()
        
        # 5. Fine-tuning 실행!
        print(f"\n🚀 Fine-tuning 시작...")
        
        self.history = self.model.fit(
            train_images,
            train_labels,
            batch_size=16,  # 작은 배치로 안정적 학습
            epochs=epochs,
            validation_data=(val_images, val_labels),
            callbacks=callbacks,
            verbose=1
        )
        
        print("\n✅ Fine-tuning 완료!")
        
        return self.history
    
    def _setup_callbacks(self):
        """Fine-tuning 콜백 설정"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Fine-tuned 모델 저장 경로
        base_name = os.path.splitext(os.path.basename(self.model_path))[0]
        finetuned_model_path = os.path.join(
            self.models_dir,
            f"{base_name}_finetuned_{timestamp}.keras"
        )
        
        callbacks = [
            # 최고 성능 모델 저장
            keras.callbacks.ModelCheckpoint(
                filepath=finetuned_model_path,
                monitor='val_loss',
                save_best_only=True,
                verbose=1
            ),
            
            # 조기 종료 (5 에포크, 짧게)
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True,
                verbose=1
            ),
            
            # 학습률 감소
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3,
                min_lr=1e-8,
                verbose=1
            )
        ]
        
        print(f"\n💾 Fine-tuned 모델 저장 경로:")
        print(f"   {finetuned_model_path}")
        
        return callbacks
    
    def evaluate(self, val_images, val_labels):
        """Fine-tuned 모델 평가"""
        print("\n" + "=" * 60)
        print("📊 Fine-tuned 모델 평가")
        print("=" * 60)
        
        loss, mae = self.model.evaluate(val_images, val_labels, verbose=0)
        
        print(f"\n검증 데이터 성능:")
        print(f"  📉 Loss (MSE): {loss:.4f}")
        print(f"  📏 MAE: {mae:.4f}")
        
        # 성능 평가 (조향값 범위: -1~1)
        if mae < 0.04:
            print(f"\n  🎉 탁월한 성능! Fine-tuning 대성공!")
        elif mae < 0.07:
            print(f"\n  ✅ 매우 좋은 성능! Fine-tuning 효과 확인!")
        elif mae < 0.10:
            print(f"\n  👍 좋은 성능!")
        else:
            print(f"\n  ⚠️ 추가 데이터나 Fine-tuning 조정 필요")
        
        # 예측 샘플 (이미 올바르게 수정되어 있음!)
        print(f"\n🎯 예측 샘플 (5개):")
        predictions = self.model.predict(val_images[:5], verbose=0)
        
        for i in range(5):
            actual = val_labels[i]
            predicted = predictions[i][0]
            error = abs(actual - predicted)
            
            print(f"  {i+1}. 실제: {actual:6.3f} | "
                f"예측: {predicted:6.3f} | "
                f"오차: {error:5.3f}")
            
    def plot_finetuning_history(self):
        """Fine-tuning 훈련 과정 그래프"""
        if self.history is None:
            print("⚠️ 훈련 기록이 없습니다!")
            return
        
        plt.figure(figsize=(12, 4))
        
        # Loss
        plt.subplot(1, 2, 1)
        plt.plot(self.history.history['loss'], label='훈련 Loss', linewidth=2)
        plt.plot(self.history.history['val_loss'], label='검증 Loss', linewidth=2)
        plt.title('Fine-tuning Loss', fontsize=14, fontweight='bold')
        plt.xlabel('에포크', fontsize=12)
        plt.ylabel('Loss', fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        
        # MAE
        plt.subplot(1, 2, 2)
        plt.plot(self.history.history['mae'], label='훈련 MAE', linewidth=2)
        plt.plot(self.history.history['val_mae'], label='검증 MAE', linewidth=2)
        plt.title('Fine-tuning MAE', fontsize=14, fontweight='bold')
        plt.xlabel('에포크', fontsize=12)
        plt.ylabel('MAE', fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 저장
        base_name = os.path.splitext(os.path.basename(self.model_path))[0]
        plot_path = os.path.join(
            self.models_dir,
            f"{base_name}_finetuning_history.png"
        )
        plt.savefig(plot_path, dpi=150)
        print(f"\n📊 Fine-tuning 그래프 저장: {plot_path}")
        
        plt.show()
    
    def save_final_model(self):
        """최종 Fine-tuned 모델 저장"""
        base_name = os.path.splitext(os.path.basename(self.model_path))[0]
        save_path = os.path.join(
            self.models_dir,
            f"{base_name}_finetuned_final.keras"
        )
        
        self.model.save(save_path)
        print(f"\n💾 최종 Fine-tuned 모델 저장: {save_path}")


# ============================================================================
# 🎓 2단계: 일반 모델 업데이트 클래스 (MobileNet 아닌 경우)
# ============================================================================

class ModelUpdater:
    """
    일반 모델 업데이트 (MobileNet이 아닌 경우)
    """
    
    def __init__(self, model_path, new_data_path, models_dir="models"):
        self.model_path = model_path
        self.new_data_path = new_data_path
        self.model = None
        self.history = None
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
    
    def load_and_update(self, epochs=20, learning_rate=0.0001):
        """일반 모델 업데이트 (B의 방식 유지)"""
        print("\n⚠️ MobileNet이 아닌 일반 모델입니다.")
        print("   일반 업데이트 방식으로 진행합니다.")
        
        # 여기서는 B의 기존 update_model 로직 사용
        # (코드 생략 - 필요시 B의 ModelUpdater 클래스 내용 복사)
        pass


# ============================================================================
# 🎓 3단계: 통합 업데이트 함수
# ============================================================================

def update_model(model_path, new_data_path, models_dir="models",
                epochs=20, learning_rate=0.00005, unfreeze_layers=20):
    """
    MobileNet 모델 업데이트 (Fine-tuning)
    
    [2단계 학습 전략]
    
    1단계: Transfer Learning (train_model.py)
    ├─ MobileNet: 고정
    ├─ Dense: 학습
    ├─ 빠른 수렴
    └─ 좋은 초기 성능
    
    2단계: Fine-tuning (이 함수) ← 지금 여기!
    ├─ MobileNet 상위: 해동
    ├─ 전체 모델: 미세 조정
    ├─ 낮은 학습률
    └─ 최고 성능
    
    [전체 흐름]
    1. 기존 MobileNet 모델 로드
    2. 새 데이터 로드
    3. 상위 레이어 해동
    4. 낮은 학습률로 Fine-tuning
    5. 성능 평가
    6. 결과 저장
    
    Args:
        model_path: 기존 모델 경로
        new_data_path: 새 데이터셋 경로
        models_dir: 모델 저장 폴더
        epochs: Fine-tuning 에포크 수 (기본 20)
        learning_rate: 학습률 (기본 0.00005, 매우 낮음!)
        unfreeze_layers: 해동할 레이어 수 (기본 20)
    """
    try:
        print("\n" + "=" * 60)
        print("🔧 MobileNet Fine-tuning")
        print("=" * 60)
        print("\n[Fine-tuning이란?]")
        print("  MobileNet의 일부를 '해동'하여 도로 인식에 특화")
        print("\n[왜 필요한가?]")
        print("  - Transfer Learning: 일반적인 특징 학습 (1단계)")
        print("  - Fine-tuning: 도로 인식에 특화 (2단계) ← 지금!")
        print("\n[설정]")
        print(f"  - 해동 레이어: 상위 {unfreeze_layers}개")
        print(f"  - 학습률: {learning_rate} (매우 낮음)")
        print(f"  - 에포크: {epochs}회")
        
        # 1️⃣ Fine-tuner 생성
        finetuner = MobileNetFineTuner(model_path, new_data_path, models_dir)
        
        # 2️⃣ 기존 모델 로드
        finetuner.load_existing_model()
        
        # 3️⃣ 새 데이터 로드
        train_images, train_labels, val_images, val_labels = finetuner.load_new_data()
        
        # 4️⃣ Fine-tuning 실행
        finetuner.fine_tune(
            train_images, train_labels,
            val_images, val_labels,
            epochs=epochs,
            learning_rate=learning_rate,
            unfreeze_layers=unfreeze_layers
        )
        
        # 5️⃣ 성능 평가
        finetuner.evaluate(val_images, val_labels)
        
        # 6️⃣ 최종 모델 저장
        finetuner.save_final_model()
        
        # 7️⃣ 그래프 생성
        finetuner.plot_finetuning_history()
        
        # 완료 메시지
        print("\n" + "=" * 60)
        print("✅ MobileNet Fine-tuning 완료!")
        print("=" * 60)
        print("\n📁 생성된 파일:")
        print("  • models/ 폴더에 Fine-tuned 모델")
        print("  • Fine-tuning 훈련 그래프")
        print("\n🎯 다음 단계:")
        print("  1. Fine-tuned 모델로 자율주행 테스트")
        print("  2. 이전 모델과 성능 비교")
        print("  3. 성능 개선 확인")
        print("\n💡 성능 비교:")
        print("  - Transfer Learning (1단계): 빠른 학습, 좋은 성능")
        print("  - Fine-tuning (2단계): 최고 성능, 도로 특화")
        
    except FileNotFoundError as e:
        print(f"\n❌ 파일을 찾을 수 없습니다: {e}")
        print("\n💡 해결 방법:")
        print("  1. 모델 파일 경로가 올바른지 확인")
        print("  2. models/ 폴더에 모델이 있는지 확인")
        print("  3. 파일 이름에 'mobilenet'이 포함되어 있는지 확인")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 해결 방법:")
        print("  1. 새 데이터셋 경로가 올바른지 확인")
        print("  2. new_dataset 폴더 구조 확인:")
        print("     new_dataset/")
        print("     ├── train/")
        print("     │   ├── images/")
        print("     │   └── annotations/")
        print("     └── validation/")
        print("         ├── images/")
        print("         └── annotations/")
        print("  3. 기존 모델이 MobileNet 기반인지 확인")


# 버전 정보
__version__ = '1.0.0'
__author__ = 'BrainAI Co,.Ltd.'
__description__ = 'BrainAI Autonomous Driving Project - MobileNet Fine-tuning Module'