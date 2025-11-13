"""
BrainAI Car [데이터 수집] 모듈_v1.0.0
PS4 컨트롤러로 BrainAI Car를 운전하면서 프레임 이미지와 조향 데이터를 수집합니다.

모듈 위치: utils/ 
모듈 이름: data_collector.py
"""

import cv2
import os
import json
import time
from datetime import datetime
from .constants import angle_to_steering

class DataCollector:
    """자율주행 학습용 데이터를 수집하는 클래스"""
    
    def __init__(self, video_prefix="brainai_car", save_fps=12, data_dir="data"):
        """
        초기화
        
        Args:
            video_prefix: 파일명 앞에 붙일 접두사
            save_fps: 초당 저장할 프레임 수 (12 = 1초에 12장)
            data_dir: 데이터 저장 폴더
        """
        self.video_prefix = video_prefix
        self.save_fps = save_fps
        self.data_dir = data_dir
        self.frame_interval = 1.0 / save_fps  # 프레임 간격
        
        # 저장 폴더 생성
        self.current_session_dir = None
        self.images_dir = None
        self.annotations_dir = None
        
        # 녹화 상태
        self.recording = False
        self.frame_count = 0
        self.total_saved = 0
        self.last_save_time = 0
        self.session_start_time = None
        self.sequence_number = 0
        
        print(f"✓ 데이터 수집기 준비 완료")
        print(f"  - 저장 위치: {self.data_dir}")
        print(f"  - 파일 접두사: {self.video_prefix}")
        print(f"  - 저장 속도: 초당 {self.save_fps}프레임")
    
    def start_recording(self, frame=None):
        """
        녹화 시작
        
        Args:
            frame: 첫 프레임 (선택사항, 사용하지 않음)
        """
        if self.recording:
            return
        
        self.recording = True
        self.frame_count = 0
        self.last_save_time = time.time()
        self.session_start_time = datetime.now()
        self.sequence_number = 0
        
        # 새 세션 폴더 생성
        session_folder_name = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        self.current_session_dir = os.path.join(self.data_dir, session_folder_name)
        self.images_dir = os.path.join(self.current_session_dir, "images")
        self.annotations_dir = os.path.join(self.current_session_dir, "annotations")
        
        # 폴더 생성
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.annotations_dir, exist_ok=True)
        
        print(f"\n🔴 녹화 시작!")
        print(f"   - 세션 폴더: {session_folder_name}")
    
    def stop_recording(self):
        """녹화 중지"""
        if not self.recording:
            return
        
        self.recording = False
        print(f"⬛ 녹화 중지! (이번 세션: {self.frame_count}장)")
        print(f" - 저장 위치: {self.current_session_dir}")
        self.frame_count = 0
    
    def save_frame(self, frame, servo_angle, speed):
        """
        프레임과 조향 데이터를 저장
        
        Args:
            frame: 카메라 이미지
            servo_angle: 서보 각도 (45~135)
            speed: 모터 속도 (참고용, 학습에는 미사용)
        """
        if not self.recording:
            return
        
        # FPS 제한 (너무 빨리 저장하지 않기)
        current_time = time.time()
        if current_time - self.last_save_time < self.frame_interval:
            return
        
        self.last_save_time = current_time
        
        image_path = None
        json_path = None
        
        # 파일명 생성 (접두사 + 타임스탬프)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename_base = f"{self.video_prefix}_{timestamp}_{self.sequence_number:04d}"
        self.sequence_number += 1
        
        # 에러 처리 추가
        try:
            # 1. 이미지 저장 (.jpg)
            image_filename = f"{filename_base}.jpg"
            image_path = os.path.join(self.images_dir, image_filename)
            success = cv2.imwrite(image_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            if not success:
                print(f"⚠️ 이미지 저장 실패!")
                return
            
            # 2. 조향 값 계산 (-1.0 ~ 1.0 범위로 변환)
            steering_value = angle_to_steering(servo_angle)

            # 3. JSON 어노테이션 저장
            annotation = {
                "image": image_filename,
                "steering": steering_value,  # AI 모델 학습용
                "servo_angle": servo_angle,  # 참고용
                "speed": speed  # 참고용 (학습에는 미사용)
            }
            
            json_filename = f"{filename_base}.json"
            json_path = os.path.join(self.annotations_dir, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(annotation, f, ensure_ascii=False)
            
            # 4. 성공했을 때만 카운트 증가
            self.frame_count += 1
            self.total_saved += 1
            
        except Exception as e:
            # 에러 나면 만든 파일 삭제 (반쪽짜리 데이터 방지)
            print(f"⚠️ 저장 오류: {e}")
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
            if json_path and os.path.exists(json_path):
                os.remove(json_path)
    
    def delete_last_files(self, count=10):
        """최근 저장된 파일 삭제"""
        if not self.images_dir or not os.path.exists(self.images_dir):
            print("⚠ 삭제할 세션이 없습니다.")
            return
        
        # 녹화 중이면 경고하지만 삭제는 허용
        if self.recording:
            print("⚠️ 녹화 중입니다. 최근 파일을 삭제합니다.")
            
        # 이미지 파일 목록 (최신순)
        images = sorted(
            [f for f in os.listdir(self.images_dir) if f.endswith('.jpg')],
            reverse=True
        )
        
        if not images:
            print("⚠ 삭제할 파일이 없습니다.")
            return
        
        # 삭제할 파일 수 제한
        delete_count = min(count, len(images))
        
        for i in range(delete_count):
            # 이미지 파일명에서 베이스명 추출
            image_file = images[i]
            base_name = os.path.splitext(image_file)[0]
            
            # 이미지 삭제
            img_path = os.path.join(self.images_dir, image_file)
            if os.path.exists(img_path):
                os.remove(img_path)
            
            # JSON 삭제
            json_file = f"{base_name}.json"
            json_path = os.path.join(self.annotations_dir, json_file)
            if os.path.exists(json_path):
                os.remove(json_path)
        
        print(f"🗑️ 최근 {delete_count}개 파일 삭제 완료")
    
    def draw_recording_indicator(self, frame):
        """녹화 중 표시"""
        if not self.recording:
            return frame
        
        height, width = frame.shape[:2]
        
        # 빨간 점 깜빡임
        if int(time.time() * 2) % 2 == 0:
            cv2.circle(frame, (width - 40, 40), 15, (0, 0, 255), -1)
        
        # REC 텍스트
        cv2.putText(
            frame, "REC", (width - 85, 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
        )
        
        # 프레임 카운트
        cv2.putText(
            frame, f"Saved: {self.frame_count}", (width - 210, 80),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
        )
        
        return frame
    
    def draw_stats(self, frame):
        """통계 정보 표시"""
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 200), (320, 270), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        
        cv2.putText(
            frame, "=== Data Collection ===", (20, 225),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
        )
        cv2.putText(
            frame, f"Total Saved: {self.total_saved}", (20, 250),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
        )
        
        return frame
    
    def cleanup(self):
        """종료 시 정리"""
        if self.recording:
            self.stop_recording()
        
        print(f"\n📊 수집 완료:")
        print(f"  - 총 저장: {self.total_saved}장")
        print(f"  - 저장 위치: {self.data_dir}")


# 버전 정보
__version__ = '1.0.0'
__author__ = 'BrainAI Co,.Ltd.'
__description__ = 'BrainAI Autonomous Driving Project'