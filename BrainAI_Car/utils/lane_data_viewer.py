"""
BrainAI Car 자율주행 도로인식 데이터 뷰어 및 불량 데이터 삭제 모듈_v1.0.0

모듈 위치: utils/ 
모듈 이름: lane_data_viewer.py

이 모듈은:
1. 이미지와 JSON 어노테이션을 시각화합니다
2. 재생/일시정지, 프레임 탐색 기능을 제공합니다
3. 불량 데이터 삭제 기능을 제공합니다 (Shift+D)

지원 폴더 구조:
1. data_merged 구조: images/ + annotations/ 하위 폴더
2. 일반 구조: 루트에 직접 .jpg + .json 파일
"""

import cv2
import json
import os
import glob
import time
import threading
import csv
from pathlib import Path
import numpy as np
from collections import deque
from datetime import datetime


class LaneDataViewer:
    """자율주행 데이터 시각화 및 정제 도구"""
    
    # 상수 정의
    DELETE_RANGE = 10  # Shift+D로 삭제할 프레임 범위 (±N)
    CACHE_REMOVE_COUNT = 10  # 캐시 초과 시 제거할 항목 수
    PRELOAD_AHEAD_FRAMES = 50  # 앞쪽으로 프리로드할 프레임 수
    PRELOAD_BEHIND_FRAMES = 10  # 뒤쪽으로 프리로드할 프레임 수
    SKIP_FRAME_COUNT = 10  # W/S 키로 건너뛸 프레임 수
            
    def __init__(self, lane_dir="data_merged_laneD1", cache_size=100):
        """
        초기화
        
        Args:
            lane_dir: 데이터 폴더 경로
            cache_size: 캐시할 프레임 개수
        """
        self.current_lane = None
        self.current_index = 0
        self.playing = False
        self.fps = 12
        self.frame_delay = 1.0 / self.fps
        self.cache_size = cache_size
        
        # 파일 매핑
        self.available_files = []
        self.image_map = {}
        self.annotation_map = {}
        self.image_files = []
        
        # 캐싱 시스템
        self.image_cache = {}
        self.annotation_cache = {}
        self.preload_queue = deque()
        self.cache_lock = threading.Lock()

        # 스레드 종료 플래그
        self.stop_preload = threading.Event()
        
        # 삭제 관련
        self.deletion_log_file = None
        self.total_deleted_count = 0  # 세션 중 삭제된 총 파일 수
        self.initial_file_count = 0   # 초기 파일 개수
        
        # 디렉토리 존재 확인
        if not os.path.exists(lane_dir):
            print(f"❌ 디렉토리를 찾을 수 없습니다: {lane_dir}")
            print("   경로를 확인해주세요.")
            return
        
        # 데이터 로드
        success = self.load_lane_data(lane_dir)
        
        if not success:
            print("❌ 데이터 로드 실패")
            return
        
        # 초기 파일 개수 저장
        self.initial_file_count = len(self.available_files)
        
        # 삭제 로그 파일 경로 설정
        self.deletion_log_file = os.path.join(self.current_lane, "deletion_log.csv")
            
        # 백그라운드 프리로딩 시작
        if self.available_files:
            try:
                self.preload_thread = threading.Thread(
                    target=self._preload_worker, 
                    daemon=True
                )
                self.preload_thread.start()
                print("   ✅ 프리로딩 스레드 시작됨")
            except Exception as e:
                print(f"⚠️  프리로딩 스레드 시작 실패: {e}")
                print("   프로그램은 계속 실행되지만 성능이 저하될 수 있습니다.")

    def load_lane_data(self, lane_dir):
        """
        이미지와 어노테이션 파일 로드
        
        Args:
            lane_dir: 데이터 폴더 경로
            
        Returns:
            bool: 성공 여부
        """
        print(f"\n📂 데이터 로드 중: {lane_dir}")
        
        try:
            self.current_lane = lane_dir
            self.current_index = 0
            
            # 폴더 구조 자동 감지
            images_subdir = os.path.join(lane_dir, "images")
            annotations_subdir = os.path.join(lane_dir, "annotations")
            
            if os.path.exists(images_subdir) and os.path.exists(annotations_subdir):
                # data_merged 구조: images/ + annotations/ 하위 폴더
                print(f"   구조: images/ + annotations/ 하위 폴더")
                search_img_dir = images_subdir
                search_ann_dir = annotations_subdir
            else:
                # 일반 구조: 루트에 직접 저장
                print(f"   구조: 루트 폴더에 직접 저장")
                search_img_dir = lane_dir
                search_ann_dir = lane_dir
            
            # 이미지 파일 찾기
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']
            self.image_files = []
            
            for ext in image_extensions:
                pattern = os.path.join(search_img_dir, ext)
                found_files = glob.glob(pattern)
                self.image_files.extend(found_files)
            
            if not self.image_files:
                print(f"❌ 이미지 파일을 찾을 수 없습니다: {search_img_dir}")
                print(f"   지원 확장자: {image_extensions}")
                return False
            
            # JSON 파일 찾기
            json_files = glob.glob(os.path.join(search_ann_dir, "*.json"))
            
            # 파일명 매핑 생성
            self.image_map = {}
            self.annotation_map = {}
            
            for img_file in self.image_files:
                base_name = Path(img_file).stem
                self.image_map[base_name] = img_file
            
            for json_file in json_files:
                base_name = Path(json_file).stem
                self.annotation_map[base_name] = json_file
            
            # 정렬된 파일 목록 생성
            self.available_files = sorted(self.image_map.keys())
            
            if not self.available_files:
                print("❌ 유효한 이미지 파일이 없습니다")
                return False
            
            # 통계 정보
            files_with_annotations = len([
                name for name in self.available_files 
                if name in self.annotation_map
            ])
            files_without_annotations = (
                len(self.available_files) - files_with_annotations
            )
            
            print(f"✅ 로드 완료:")
            print(f"   - 총 이미지: {len(self.available_files)}개")
            print(f"   - JSON 있음: {files_with_annotations}개")
            if files_without_annotations > 0:
                print(f"   - JSON 없음: {files_without_annotations}개")
            
            # 첫 배치 프리로드
            self._queue_preload(0, min(50, len(self.available_files)))
            
            return True
            
        except Exception as e:
            print(f"❌ 데이터 로드 오류: {e}")
            self.available_files = []
            return False
    
    def delete_frames_around_current(self, range_size=None):
        """
        현재 프레임 기준 앞뒤 range_size 프레임 즉시 삭제
        
        Args:
            range_size: 현재 프레임 기준 앞뒤로 삭제할 프레임 개수
                    (None이면 DELETE_RANGE 사용)
        
        Returns:
            int: 삭제된 파일 개수
        """
        if range_size is None:
            range_size = self.DELETE_RANGE
    
        if not self.available_files:
            print("❌ 삭제할 데이터가 없습니다.")
            return 0
       
        start_idx = max(0, self.current_index - range_size)
        end_idx = min(len(self.available_files) - 1, self.current_index + range_size)
        
        # 삭제 대상 파일 목록 생성
        files_to_delete = []
        for idx in range(start_idx, end_idx + 1):
            file_base = self.available_files[idx]
            
            if file_base in self.image_map:
                files_to_delete.append(self.image_map[file_base])
            
            if file_base in self.annotation_map:
                files_to_delete.append(self.annotation_map[file_base])
        
        if not files_to_delete:
            print("❌ 삭제할 파일이 없습니다.")
            return 0
        
        # 즉시 삭제 실행
        deleted_count = self._execute_deletion(files_to_delete)
        
        return deleted_count
    
    def _execute_deletion(self, files_to_delete):
        """
        실제 파일 삭제 실행
        
        Args:
            files_to_delete: 삭제할 파일 경로 리스트
            
        Returns:
            int: 삭제된 파일 개수
        """
        deleted_files = []
        failed_files = []
        
        for file_path in files_to_delete:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_files.append(file_path)
            except Exception as e:
                print(f"❌ 삭제 실패: {os.path.basename(file_path)} - {e}")
                failed_files.append(file_path)
        
        # 삭제 로그 저장
        if deleted_files:
            self._save_deletion_log(deleted_files)
            self.total_deleted_count += len(deleted_files)
        
        # 결과 출력
        print(f"\n✅ 총 {len(deleted_files)}개 파일 삭제됨")
        if failed_files:
            print(f"⚠️  실패: {len(failed_files)}개 파일")
        
        # 캐시 클리어 및 데이터 재로드
        with self.cache_lock:
            self.image_cache.clear()
            self.annotation_cache.clear()
            self.preload_queue.clear()
        
        # 데이터 재로드
        self.load_lane_data(self.current_lane)
                
        # 현재 인덱스를 삭제 범위 끝 다음으로 조정
        if self.current_index >= len(self.available_files):
            self.current_index = max(0, len(self.available_files) - 1)
        else:
            # 삭제된 구간을 건너뛰고 다음 프레임으로 이동
            # (삭제 전 end_idx + 1에 해당하는 위치)
            pass  # 현재 인덱스 유지 (재로드 후 자동으로 조정됨)

        print(f"📍 현재 위치: {self.current_index + 1}/{len(self.available_files)}")
        
        return len(deleted_files)
    
    def _save_deletion_log(self, deleted_files):
        """
        삭제 로그를 CSV 파일로 저장
        
        Args:
            deleted_files: 삭제된 파일 경로 리스트
        """
        try:
            # 로그 파일이 없으면 헤더 작성
            file_exists = os.path.exists(self.deletion_log_file)
            
            with open(self.deletion_log_file, 'a', 
                     newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    writer.writerow(['timestamp', 'frame_index', 'deleted_file'])
                
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                for file_path in deleted_files:
                    writer.writerow([
                        timestamp, 
                        self.current_index, 
                        os.path.basename(file_path)
                    ])
            
            print(f"📝 삭제 로그 저장: {self.deletion_log_file}")
            
        except Exception as e:
            print(f"⚠️  로그 저장 실패: {e}")
    
    def _queue_preload(self, start_idx, end_idx):
        """
        프리로딩 큐에 이미지 추가
        
        Args:
            start_idx: 시작 인덱스
            end_idx: 종료 인덱스
        """
        for i in range(start_idx, min(end_idx, len(self.available_files))):
            if i not in self.image_cache:
                self.preload_queue.append(i)
    
    def _preload_worker(self):
        """백그라운드 스레드로 이미지 프리로드"""
        while not self.stop_preload.is_set():  # 종료 조건 추가
            try:
                if self.preload_queue:
                    idx = self.preload_queue.popleft()
                    self._load_frame_data(idx)
                else:
                    time.sleep(0.01)
            except Exception as e:
                if not self.stop_preload.is_set():  # 종료 중이 아닐 때만 출력
                    print(f"⚠️  프리로드 오류: {e}")
                time.sleep(0.1)
                
    def _load_frame_data(self, index):
        """
        단일 프레임 데이터 로드 및 캐싱
        
        Args:
            index: 프레임 인덱스
            
        Returns:
            tuple: (이미지, steering 값)
        """
        if index >= len(self.available_files):
            return None, None
        
        current_file = self.available_files[index]
        
        # 캐시 확인
        with self.cache_lock:
            if index in self.image_cache:
                return self.image_cache[index], self.annotation_cache[index]
        
        # 이미지 로드
        img_path = self.image_map[current_file]
        image = cv2.imread(img_path)
        
        if image is None:
            print(f"❌ 이미지 로드 실패: {img_path}")
            return None, None
        
        # 어노테이션 로드
        steering = None
        if current_file in self.annotation_map:
            json_path = self.annotation_map[current_file]
            steering = self.load_annotation(json_path)
        
        # 캐시에 저장 (크기 제한)
        with self.cache_lock:
            if len(self.image_cache) >= self.cache_size:
                # 현재 인덱스에서 먼 항목부터 제거
                sorted_keys = sorted(
                    self.image_cache.keys(),
                    key=lambda k: abs(k - index) # 거리 오름차순
                )
                # 뒤에서 N개 = 거리가 가장 먼 N개
                keys_to_remove = sorted_keys[-self.CACHE_REMOVE_COUNT:]
                for key in keys_to_remove:
                    del self.image_cache[key]
                    del self.annotation_cache[key]
                    
            self.image_cache[index] = image
            self.annotation_cache[index] = steering
        
        return image, steering
    
    def load_annotation(self, json_file):
        """
        JSON 파일에서 steering 값 로드
        
        Args:
            json_file: JSON 파일 경로
            
        Returns:
            float: steering 값 (없으면 None)
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('steering', 0.0)
        except Exception as e:
            print(f"⚠️  어노테이션 로드 실패 {json_file}: {e}")
            return None
    
    def draw_steering_indicator(self, image, steering_value):
        """
        이미지에 steering 표시기 및 UI 오버레이 그리기
        
        Args:
            image: 원본 이미지
            steering_value: steering 값 (-1.0 ~ 1.0)
            
        Returns:
            numpy.ndarray: 표시기가 그려진 이미지
        """
        # 캐시된 이미지 수정 방지를 위해 복사
        display_image = image.copy()
        height, width = display_image.shape[:2]
        
        # === 상단 헤더 배경 (반투명 검은색) ===
        overlay = display_image.copy()
        cv2.rectangle(overlay, (0, 0), (width, 70), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, display_image, 0.3, 0, display_image)
        
        # === 프레임 진행률 (좌측 상단, 크고 선명하게) ===
        progress_text = (
            f"Frame: {self.current_index + 1}/{len(self.available_files)} "
            f"({(self.current_index + 1) / len(self.available_files) * 100:.1f}%)"
        )
        cv2.putText(
            display_image, progress_text, (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2  # 노란색
        )
        
        # === 재생 상태 (우측 상단) ===
        status_text = "PLAYING" if self.playing else "PAUSED"
        status_color = (0, 255, 0) if self.playing else (100, 100, 255)
        
        (status_width, _), _ = cv2.getTextSize(
            status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2
        )
        
        cv2.putText(
            display_image, status_text, 
            (width - status_width - 20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, status_color, 2
        )
        
        # === 작업 통계 (우측 상단 작은 글씨) ===
        if self.total_deleted_count > 0:
            deleted_percent = (self.total_deleted_count / self.initial_file_count * 100)
            stats_text = f"Deleted: {self.total_deleted_count} ({deleted_percent:.1f}%)"
            
            (stats_width, _), _ = cv2.getTextSize(
                stats_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            
            cv2.putText(
                display_image, stats_text, 
                (width - stats_width - 20, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 150, 255), 1
            )
        
        # === Steering 표시기 ===
        if steering_value is not None:
            # 화면 하단 75% 위치
            y_position = int(height * 0.75)
            
            # Steering 값을 x 좌표로 변환 (-1~1 → 0~width)
            cx = int((steering_value + 1) / 2 * width)
            
            # 중앙에서 steering 위치까지 선 그리기
            cv2.line(
                display_image, 
                (width // 2, height), 
                (cx, y_position), 
                (0, 0, 255), 4
            )
            
            # Steering 위치에 원 그리기
            cv2.circle(
                display_image, 
                (cx, y_position), 
                10, (0, 255, 0), -1
            )
            
            # Steering 값 표시 (하단 중앙, 배경 있음)
            text = f"Steering: {steering_value:.3f}"
            (text_w, text_h), baseline = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2
            )
            
            # 배경 박스
            box_x = (width - text_w) // 2 - 10
            box_y = height - text_h - 25
            box_w = text_w + 20
            box_h = text_h + 15
            
            cv2.rectangle(
                display_image, 
                (box_x, box_y),
                (box_x + box_w, box_y + box_h),
                (0, 0, 0), -1
            )
            
            cv2.rectangle(
                display_image, 
                (box_x, box_y),
                (box_x + box_w, box_y + box_h),
                (0, 255, 0), 2
            )
            
            # 텍스트
            text_x = (width - text_w) // 2
            text_y = height - 20
            
            cv2.putText(
                display_image, text, (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2
            )
        else:
            # 어노테이션 없음 표시
            text = "No Annotation"
            (text_w, text_h), baseline = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2
            )
            
            # 배경 박스
            box_x = (width - text_w) // 2 - 10
            box_y = height - text_h - 25
            box_w = text_w + 20
            box_h = text_h + 15
            
            cv2.rectangle(
                display_image, 
                (box_x, box_y),
                (box_x + box_w, box_y + box_h),
                (0, 0, 0), -1
            )
            
            cv2.rectangle(
                display_image, 
                (box_x, box_y),
                (box_x + box_w, box_y + box_h),
                (0, 0, 255), 2
            )
            
            # 텍스트
            text_x = (width - text_w) // 2
            text_y = height - 20
            
            cv2.putText(
                display_image, text, (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2
            )
        
        # === 하단 단축키 안내 (간결하게 1줄) ===
        help_overlay = display_image.copy()
        cv2.rectangle(help_overlay, (0, height - 85), (width, height - 70), (0, 0, 0), -1)
        cv2.addWeighted(help_overlay, 0.6, display_image, 0.4, 0, display_image)
        
        help_text = "[W/S] 10Frames  [Shift+D] Delete +/-10Frames  [Space] Play/Pause  [Q] Quit"
        (help_w, _), _ = cv2.getTextSize(help_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        
        cv2.putText(
            display_image, help_text, 
            ((width - help_w) // 2, height - 73),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1
        )
        
        return display_image
    
    def display_current_frame(self):
        """
        현재 프레임 표시
        
        Returns:
            numpy.ndarray: 표시할 프레임 (없으면 None)
        """
        if not self.available_files or self.current_index >= len(self.available_files):
            return None
        
        # 캐시에서 로드 또는 새로 로드
        image, steering = self._load_frame_data(self.current_index)
        
        if image is None:
            return None
        
        # 주변 프레임 프리로드 큐에 추가
        start_preload = max(0, self.current_index - self.PRELOAD_BEHIND_FRAMES)
        end_preload = min(len(self.available_files), self.current_index + self.PRELOAD_AHEAD_FRAMES)
        self._queue_preload(start_preload, end_preload)
        
        # 어노테이션 그리기
        annotated_image = self.draw_steering_indicator(image, steering)
        
        return annotated_image
    
    def next_frame(self):
        """다음 프레임으로 이동"""
        if self.available_files and self.current_index < len(self.available_files) - 1:
            self.current_index += 1
        elif self.available_files:
            self.current_index = 0  # 처음으로 루프
    
    def previous_frame(self):
        """이전 프레임으로 이동"""
        if self.available_files and self.current_index > 0:
            self.current_index -= 1
        elif self.available_files:
            self.current_index = len(self.available_files) - 1  # 끝으로 루프
    
    def skip_forward(self, count=10):
        """
        앞으로 건너뛰기
        
        Args:
            count: 건너뛸 프레임 수
        """
        if self.available_files:
            self.current_index = min(
                self.current_index + count, 
                len(self.available_files) - 1
            )
    
    def skip_backward(self, count=10):
        """
        뒤로 건너뛰기
        
        Args:
            count: 건너뛸 프레임 수
        """
        if self.available_files:
            self.current_index = max(self.current_index - count, 0)
    
    def run(self):
        """메인 애플리케이션 루프"""
        if not self.available_files:
            return
        
        cv2.namedWindow('BrainAI Car AD dataClean', cv2.WINDOW_AUTOSIZE)
        
        # 사용 안내 (간소화)
        print("\n" + "=" * 60)
        print("🚗 BrainAI Car AD dataClean")
        print("=" * 60)
        print("\n📋 핵심 기능:")
        print("  Space      - 재생/정지")
        print("  ← →       - 1프레임 이동")
        print("  W / S      - 10프레임 앞으로/뒤로")
        print("  Shift+D    - 🗑️  현재 ±10 프레임 삭제")
        print("  + / -      - 재생 속도 조절")
        print("  Q / ESC    - 종료")
        print("=" * 60)
        print(f"\n✅ 준비 완료: {len(self.available_files)}개 프레임 로드됨\n")
        
        last_frame_time = time.time()
        
        try:
            while True:
                # 현재 프레임 표시
                frame = self.display_current_frame()
                
                if frame is not None:
                    cv2.imshow('BrainAI Car AD dataClean', frame)
                else:
                    # 에러 메시지 표시
                    error_img = np.zeros((400, 800, 3), dtype=np.uint8)
                    cv2.putText(
                        error_img, "Failed to load current frame", 
                        (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 
                        1, (0, 0, 255), 2
                    )
                    cv2.imshow('BrainAI Car AD dataClean', error_img)
                
                # 자동 재생
                if self.playing:
                    current_time = time.time()
                    if current_time - last_frame_time >= self.frame_delay:
                        self.next_frame()
                        last_frame_time = current_time
                
                # 키보드 입력 처리
                key = cv2.waitKey(30) & 0xFF
                
                # 종료
                if key == ord('q') or key == ord('Q') or key == 27:  # ESC
                    print("\n종료합니다...")
                    break
                
                # 재생/정지
                elif key == ord(' '):
                    self.playing = not self.playing
                    status = "▶ Playing" if self.playing else "⏸ Paused"
                    print(f"{status}")
                
                # 삭제 기능 (Shift+D) - 즉시 삭제
                elif key == ord('D'):
                    self.playing = False  # 재생 중지
                    deleted_count = self.delete_frames_around_current()
                    if deleted_count > 0:
                        print(f"🗑️  삭제 완료!")
                    else:
                        print("❌ 삭제할 파일이 없습니다")
                
                # 10프레임 이동 (W/S)
                elif key == ord('w') or key == ord('W'):
                    self.skip_forward(self.SKIP_FRAME_COUNT)
                    print(f"⏩ 10프레임 앞으로: {self.current_index + 1}")
                
                elif key == ord('s') or key == ord('S'):
                    self.skip_backward(self.SKIP_FRAME_COUNT)
                    print(f"⏪ 10프레임 뒤로: {self.current_index + 1}")
                
                # FPS 조정
                elif key == ord('+') or key == ord('='):
                    self.fps = min(self.fps + 2, 60)
                    self.frame_delay = 1.0 / self.fps
                    print(f"⚡ 재생 속도: {self.fps} FPS")
                
                elif key == ord('-'):
                    self.fps = max(self.fps - 2, 1)
                    self.frame_delay = 1.0 / self.fps
                    print(f"⚡ 재생 속도: {self.fps} FPS")
                
                # 방향키
                elif key == 81:  # Left arrow
                    self.previous_frame()
                elif key == 83:  # Right arrow
                    self.next_frame()
                
                # 윈도우가 닫혔는지 확인
                try:
                    if cv2.getWindowProperty('BrainAI Car AD dataClean', cv2.WND_PROP_VISIBLE) < 1:
                        break
                except cv2.error:
                    # 윈도우가 이미 닫힘
                    break
        
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단됨")
        except Exception as e:
            print(f"❌ 메인 루프 오류: {e}")
        finally:
            # 스레드 종료 신호
            self.stop_preload.set()
            if hasattr(self, 'preload_thread'):
                self.preload_thread.join(timeout=1.0)
                
            # 정리
            cv2.destroyAllWindows()
            
            # 최종 통계 출력
            print("\n" + "=" * 60)
            print("📊 작업 완료 통계")
            print("=" * 60)
            print(f"초기 파일 수: {self.initial_file_count}개")
            print(f"삭제된 파일: {self.total_deleted_count}개")
            print(f"남은 파일 수: {len(self.available_files)}개")
            
            if self.total_deleted_count > 0:
                deletion_rate = (self.total_deleted_count / self.initial_file_count * 100)
                print(f"삭제 비율: {deletion_rate:.1f}%")
            
            print("=" * 60)
            print("프로그램 종료")


if __name__ == "__main__":
    # 직접 실행 시 테스트
    viewer = LaneDataViewer("data_merged_laneD1", cache_size=200)
    viewer.run()


# 버전 정보
__version__ = '1.0.0'
__author__ = 'BrainAI Co,.Ltd.'
__description__ = 'BrainAI Autonomous Driving Project - Data Viewer Module (Improved UI)'