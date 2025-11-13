"""
BrainAI Car 자율주행 도로인식 데이터셋 생성_v1.0.0

모듈 위치: utils/ 
모듈 이름: create_dataset.py

이 모듈은:
1. data 폴더의 이미지와 JSON을 읽어서
2. train과 validation으로 자동 분할합니다 (70:30)
"""

import os
import json
import random
import shutil
import math
from pathlib import Path

def create_dataset(source_dir, target_dir, train_ratio=0.7):
    """
    데이터셋 생성
    
    Args:
        source_dir: 획득한 데이터 폴더
        target_dir: 저장할 데이터셋 폴더
        train_ratio: 훈련 데이터 비율 (0.7 = 70%)
    """
    
    # train_ratio 검증 추가
    if not 0 < train_ratio < 1:
        print(f"❌ 오류: train_ratio는 0과 1 사이의 값이어야 합니다: {train_ratio}")
        return
    
    # 1. 폴더 확인
    images_dir = os.path.join(source_dir, "images")
    annotations_dir = os.path.join(source_dir, "annotations")
    
    if not os.path.exists(images_dir):
        print(f"❌ 이미지 폴더를 찾을 수 없습니다: {images_dir}")
        print("   먼저 BrainAI_Car_AD_dataAcquisition.py로 데이터를 획득하세요!")
        return
    
    # 2. 출력 폴더 생성
    train_img_dir = os.path.join(target_dir, "train", "images")
    train_ann_dir = os.path.join(target_dir, "train", "annotations")
    val_img_dir = os.path.join(target_dir, "validation", "images")
    val_ann_dir = os.path.join(target_dir, "validation", "annotations")
    
    for folder in [train_img_dir, train_ann_dir, val_img_dir, val_ann_dir]:
        os.makedirs(folder, exist_ok=True)
    
    # 3. 이미지와 JSON 쌍 찾기
    print(f"\n📂 이미지 스캔 중: {images_dir}")
    
    valid_pairs = []
    img_files = [f for f in os.listdir(images_dir) if f.endswith('.jpg')]
    total_images = len(img_files)
    print(f"   총 {total_images}개 이미지 발견")
    
    for idx, img_file in enumerate(img_files, 1):
        # 진행률 표시 (100개마다)
        if idx % 100 == 0 or idx == total_images:
            progress = (idx / total_images) * 100
            print(f"   진행중... {idx}/{total_images} ({progress:.1f}%)", end='\r')
        
        # 대응하는 JSON 찾기
        base_name = os.path.splitext(img_file)[0]
        json_file = f"{base_name}.json"
        
        img_path = os.path.join(images_dir, img_file)
        json_path = os.path.join(annotations_dir, json_file)
        
        # JSON이 있고, 모든 필수 데이터가 유효한지 확인
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 필수 필드 확인
                    required_fields = ['steering']
                    if not all(field in data for field in required_fields):
                        print(f"⚠️  필수 필드 누락: {json_file}")
                        continue

                    # 숫자 값 유효성 확인
                    try:
                        steering = float(data['steering'])
                        
                        # NaN, Infinity 체크
                        if math.isnan(steering) or math.isinf(steering):
                            print(f"⚠️  비정상 값 (NaN/Inf): {json_file}")
                            continue
                            
                    except (ValueError, TypeError):
                        print(f"⚠️  숫자 변환 실패: {json_file}")
                        continue
                    
                    # 모든 검증 통과
                    valid_pairs.append((img_path, json_path))
                    
            except json.JSONDecodeError:
                print(f"⚠️  JSON 파싱 실패: {json_file}")
                continue
            except Exception as e:
                print(f"⚠️  오류 ({json_file}): {str(e)}")
                continue
    
    print()  # 진행률 출력 후 줄바꿈
    
    if not valid_pairs:
        print("❌ 유효한 데이터를 찾을 수 없습니다!")
        return
    
    print(f"✅ 발견: {len(valid_pairs)}개 데이터")
    
    # 4. 랜덤 셔플
    random.shuffle(valid_pairs)
    
    # 5. Train/Validation 분할
    split_idx = int(len(valid_pairs) * train_ratio)
    train_pairs = valid_pairs[:split_idx]
    val_pairs = valid_pairs[split_idx:]
    
    print(f"\n📊 분할:")
    print(f"  - Train: {len(train_pairs)}개 ({len(train_pairs)/len(valid_pairs)*100:.1f}%)")
    print(f"  - Validation: {len(val_pairs)}개 ({len(val_pairs)/len(valid_pairs)*100:.1f}%)")
    
    # 6. 파일 복사
    print(f"\n📥 복사 중...")
    
    # Train 복사
    print(f"   Train 데이터 복사 중... (0/{len(train_pairs)})", end='\r')
    for idx, (img_path, json_path) in enumerate(train_pairs, 1):
        shutil.copy2(img_path, train_img_dir)
        shutil.copy2(json_path, train_ann_dir)
        if idx % 100 == 0 or idx == len(train_pairs):
            print(f"   Train 데이터 복사 중... ({idx}/{len(train_pairs)})", end='\r')
    print()
    
    # Validation 복사
    print(f"   Validation 데이터 복사 중... (0/{len(val_pairs)})", end='\r')
    for idx, (img_path, json_path) in enumerate(val_pairs, 1):
        shutil.copy2(img_path, val_img_dir)
        shutil.copy2(json_path, val_ann_dir)
        if idx % 100 == 0 or idx == len(val_pairs):
            print(f"   Validation 데이터 복사 중... ({idx}/{len(val_pairs)})", end='\r')
    print()
    
    print(f"✅ 완료!")
    
    # 7. 최종 구조 표시
    print(f"\n📂 저장 위치: {target_dir}")
    print(f"└── train/")
    print(f"    ├── images/ ({len(train_pairs)}개)")
    print(f"    └── annotations/ ({len(train_pairs)}개)")
    print(f"└── validation/")
    print(f"    ├── images/ ({len(val_pairs)}개)")
    print(f"    └── annotations/ ({len(val_pairs)}개)")
    
    print("\n✅ 다음 단계: python main/BrainAI_Car_AD_modeling.py 실행")


# 버전 정보
__version__ = '1.0.0'
__author__ = 'BrainAI Co,.Ltd.'
__description__ = 'BrainAI Autonomous Driving Project - Dataset Creation Module'