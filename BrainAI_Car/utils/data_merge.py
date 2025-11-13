"""
BrainAI Car 자율주행 - 데이터 병합 모듈
고등학생 교육용 버전 v1.0.0

이 파일은 실제 데이터 병합 작업을 수행하는 함수들이 들어있어요.

📚 주요 개념:
- 모듈(Module): 여러 함수를 담은 파일. 다른 곳에서 불러서 사용 가능
- 함수(Function): 특정 작업을 수행하는 코드 묶음
"""

import os
import shutil
from pathlib import Path


def merge_data_folders(data_root, target_dir):
    """
    여러 날짜 폴더에 나뉜 데이터를 하나로 합치는 함수
    
    🎯 이 함수가 하는 일:
    1. data 폴더 안의 모든 날짜 폴더를 찾기
    2. 각 폴더에서 이미지(.jpg)와 라벨(.json) 파일 찾기
    3. 파일명이 중복되면 자동으로 이름 바꾸기
    4. 모든 파일을 하나의 폴더에 복사하기
    
    Args:
        data_root: 원본 데이터 폴더 경로 (예: 'data_laneD1')
        target_dir: 합친 데이터를 저장할 폴더 (예: 'data_merged_laneD1')
    
    📖 용어 설명:
    - Args: Arguments(인수) - 함수에 넣어주는 값
    - 파일 경로: 컴퓨터에서 파일의 위치를 나타내는 주소
    """
    
    print("\n" + "=" * 60)
    print("🤖 BrainAI Car 자율주행 - 데이터 병합 시작")
    print("=" * 60)
    
    # ========================================
    # 1단계: data 폴더가 있는지 확인
    # ========================================
    if not os.path.exists(data_root):
        print(f"\n❌ 오류: data 폴더를 찾을 수 없습니다: {data_root}")
        print(f"\n💡 힌트:")
        print(f"   1. 폴더 이름을 확인해보세요")
        print(f"   2. 프로젝트 루트 폴더에서 실행하고 있는지 확인하세요")
        return
    
    # ========================================
    # 2단계: 유효한 날짜 폴더 찾기
    # ========================================
    print(f"\n🔍 '{data_root}' 폴더에서 데이터 찾는 중...")
    
    date_folders = []  # 날짜 폴더 이름들을 담을 리스트
    
    # data_root 안의 모든 항목(폴더/파일) 확인
    for item in os.listdir(data_root):
        item_path = os.path.join(data_root, item)
        
        # 폴더인지 확인
        if os.path.isdir(item_path):
            # images와 annotations 폴더가 둘 다 있는지 확인
            images_path = os.path.join(item_path, "images")
            annotations_path = os.path.join(item_path, "annotations")
            
            if os.path.exists(images_path) and os.path.exists(annotations_path):
                date_folders.append(item)  # 유효한 폴더로 추가
    
    # 날짜 폴더가 하나도 없으면 종료
    if not date_folders:
        print(f"\n❌ 오류: 유효한 데이터 폴더를 찾을 수 없습니다!")
        print(f"\n💡 필요한 구조:")
        print(f"   {data_root}/")
        print(f"   ├── 20250704_183905/")
        print(f"   │   ├── images/")
        print(f"   │   └── annotations/")
        print(f"   └── 20250704_190000/")
        print(f"       ├── images/")
        print(f"       └── annotations/")
        return
    
    date_folders.sort()  # 날짜순으로 정렬
    
    # 발견된 폴더 정보 출력
    print(f"\n📂 발견된 데이터 폴더: {len(date_folders)}개")
    for folder in date_folders:
        folder_path = os.path.join(data_root, folder)
        # 이미지 개수 세기
        img_count = len([f for f in os.listdir(os.path.join(folder_path, "images")) 
                         if f.endswith('.jpg')])
        print(f"   - {folder} ({img_count}개 이미지)")
    
    # ========================================
    # 3단계: 결과를 저장할 폴더 만들기
    # ========================================
    target_images_dir = os.path.join(target_dir, "images")
    target_annotations_dir = os.path.join(target_dir, "annotations")
    
    # 폴더가 없으면 생성 (이미 있으면 그대로 사용)
    os.makedirs(target_images_dir, exist_ok=True)
    os.makedirs(target_annotations_dir, exist_ok=True)
    
    print(f"\n📁 결과 저장 폴더 생성 완료:")
    print(f"   - {target_images_dir}")
    print(f"   - {target_annotations_dir}")
    
    # ========================================
    # 4단계: 파일 중복 방지 준비
    # ========================================
    # 이미 복사한 파일명을 기억하기 위한 세트
    existing_files = set()
    
    # 통계를 위한 카운터
    total_images = 0
    total_annotations = 0
    
    # ========================================
    # 5단계: 각 날짜 폴더에서 데이터 복사
    # ========================================
    for idx, folder_name in enumerate(date_folders, 1):
        print(f"\n📥 [{idx}/{len(date_folders)}] 처리 중: {folder_name}")
        
        # 현재 폴더의 images, annotations 경로
        source_images_dir = os.path.join(data_root, folder_name, "images")
        source_annotations_dir = os.path.join(data_root, folder_name, "annotations")
        
        # 이미지 파일 목록 가져오기
        img_files = [f for f in os.listdir(source_images_dir) if f.endswith('.jpg')]
        
        print(f"   발견: {len(img_files)}개 이미지")
        
        copied_count = 0  # 이 폴더에서 복사한 파일 수
        
        # 각 이미지 파일 처리
        for img_file in img_files:
            # 이미지 파일명에서 확장자를 제외한 부분 (예: "image_001.jpg" → "image_001")
            base_name = os.path.splitext(img_file)[0]
            json_file = f"{base_name}.json"
            
            # 원본 파일 경로
            source_img_path = os.path.join(source_images_dir, img_file)
            source_json_path = os.path.join(source_annotations_dir, json_file)
            
            # JSON 파일이 없으면 이미지도 건너뛰기
            # (이미지와 라벨은 항상 쌍으로 있어야 함)
            if not os.path.exists(source_json_path):
                continue
            
            # --------------------------------------
            # 중복 파일명 처리
            # --------------------------------------
            target_img_name = img_file
            target_json_name = json_file
            
            # 같은 이름의 파일이 이미 있다면?
            if img_file in existing_files:
                # 폴더명을 앞에 붙여서 구분
                base = os.path.splitext(img_file)[0]
                ext = os.path.splitext(img_file)[1]
                target_img_name = f"{folder_name}_{base}{ext}"
                target_json_name = f"{folder_name}_{base}.json"
                
                # 그래도 중복이면 숫자를 붙임 (_1, _2, _3, ...)
                counter = 1
                while target_img_name in existing_files:
                    target_img_name = f"{folder_name}_{base}_{counter}{ext}"
                    target_json_name = f"{folder_name}_{base}_{counter}.json"
                    counter += 1
            
            # 사용한 파일명 기록 (다음 중복 체크를 위해)
            existing_files.add(target_img_name)
            
            # --------------------------------------
            # 파일 복사
            # --------------------------------------
            target_img_path = os.path.join(target_images_dir, target_img_name)
            target_json_path = os.path.join(target_annotations_dir, target_json_name)
            
            # shutil.copy2: 파일을 복사 (메타데이터 포함)
            shutil.copy2(source_img_path, target_img_path)
            shutil.copy2(source_json_path, target_json_path)
            
            copied_count += 1
            
            # 진행 상황 표시 (100개마다)
            if copied_count % 100 == 0 or copied_count == len(img_files):
                print(f"   복사 중... {copied_count}/{len(img_files)}개", end='\r')
        
        print(f"   ✅ 복사 완료: {copied_count}개 쌍 (이미지 + JSON)")
        total_images += copied_count
        total_annotations += copied_count
    
    # ========================================
    # 6단계: 최종 결과 출력
    # ========================================
    print(f"\n" + "=" * 60)
    print(f"🎉 병합 완료!")
    print(f"=" * 60)
    
    print(f"\n📊 병합 결과:")
    print(f"   - 처리된 날짜 폴더: {len(date_folders)}개")
    print(f"   - 총 이미지: {total_images}개")
    print(f"   - 총 어노테이션: {total_annotations}개")
    
    print(f"\n📂 저장 위치: {target_dir}/")
    print(f"   ├── images/ ({total_images}개)")
    print(f"   └── annotations/ ({total_annotations}개)")
    
    print("\n💡 다음 단계:")
    print("   데이터 탐색 스크립트를 실행해보세요!")
    print(f"   (source_dir을 '{target_dir}'로 설정)")


# ============================================================
# 모듈 정보
# ============================================================
__version__ = '1.0.0'
__author__ = 'BrainAI Co,.Ltd.'
__description__ = 'BrainAI Autonomous Driving Project - Data Merge Module'