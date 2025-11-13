"""
BrainAI Car [PS4CarDataCollector] 모듈_v1.1.0
PS4 컨트롤러로 BrainAI Car를 운전하면서 데이터를 획득하는 핵심 기능

모듈 위치: / 
모듈 이름: ps4car_data_collector.py

변경사항 v1.1.0:
- process_events()에 frame 전달하여 R1/L1 버튼 자동 처리
"""

import time
import cv2
import math

from .constants import SPEED_DEFAULT
from .car_controller import BrainAICarController
from .ps4_controller import PS4Controller

class PS4CarDataCollector:
    """PS4 컨트롤러로 자동차를 운전하면서 데이터를 수집하는 클래스"""
    
    def __init__(self, video_source=0, initial_speed=SPEED_DEFAULT):
        """
        초기화
        
        Args:
            video_source: 비디오 소스
                - 0: 내장 웹캠
                - 'http://IP주소:8080/video': IP 웹캠
            initial_speed: 기본 전진 속도 (181~1023)
        """
        self.video_source = video_source
        
        print('\n' + '=' * 60)
        print('    BrainAI Car - PS4 컨트롤러 데이터 수집')
        print('=' * 60)
        
        # 1. 자동차 컨트롤러 초기화 (녹화 기능 활성화)
        print('\n[1단계] 자동차 연결 중...')
        self.car = BrainAICarController(
            video_source=video_source,
            initial_speed=initial_speed,
            use_serial=True,
            show_messages=True,
            enable_recording=True  # 🔴 녹화 기능 활성화
        )
        self.car.connect_microbit()
        
        # 2. PS4 컨트롤러 초기화
        print('\n[2단계] PS4 컨트롤러 연결 중...')
        self.ps4 = PS4Controller(self.car)
        
        # 카메라 실패 카운터 추가
        self.frame_fail_count = 0
    
    def run(self):
        """메인 제어 루프를 실행합니다."""
        
        # 컨트롤러 연결 확인
        if not self.ps4.connected:
            print('\n❌ PS4 컨트롤러가 연결되지 않았습니다.')
            print('\n📌 연결 방법:')
            print('  1. PS4 컨트롤러의 SHARE + PS 버튼을 동시에 3초간 누르기')
            print('  2. 컴퓨터의 Bluetooth 설정에서 "Wireless Controller" 연결')
            print('  3. 연결 후 다시 프로그램 실행')
            return
        
        # 조작 방법 안내
        self._show_instructions()
        
        # 비디오 캡처 시작
        self.car.video_capture = cv2.VideoCapture(self.video_source)
        
        if not self.car.video_capture.isOpened():
            print('\n❌ 비디오 소스를 열 수 없습니다.')
            print(f'   비디오 소스: {self.video_source}')
            self.cleanup()
            return
        
        print('\n✓ 모든 준비 완료!')
        print('컨트롤러로 자동차를 조종하고 R1으로 녹화하세요!\n')
        
        # 메인 루프
        frame_count = 0
        fps_start_time = time.time()
        fps = 0
        
        try:
            while True:
                # 프레임 읽기
                ret, frame = self.car.video_capture.read()

                if not ret:  # ← 실패 확인
                    self.frame_fail_count += 1
                    print(f'⚠ 프레임 읽기 실패 ({self.frame_fail_count}번째)')
                    
                    # 100번 연속 실패하면 종료
                    if self.frame_fail_count > 100:
                        print('\n❌ 카메라 연결 끊김 - 프로그램 종료합니다')
                        self.cleanup()
                        return
                    
                    time.sleep(0.1)
                    continue  # ← 다음 반복으로

                # 성공하면 카운터 초기화
                self.frame_fail_count = 0
                
                # FIXED: PS4 컨트롤러 입력 처리 (R1, L1 자동 처리)
                # R1: 녹화 토글
                # L1: 최근 10개 프레임 삭제
                self.ps4.process_events(frame)  # ← Pass frame here!
                
                # 녹화 중이면 프레임 저장
                self.car.save_data_frame(frame)
                
                # FPS 계산
                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = time.time() - fps_start_time
                    fps = 30 / elapsed if elapsed > 0 else 0
                    fps_start_time = time.time()
                
                # 화면에 상태 정보 표시
                frame = self._draw_status(frame, fps)
                
                # 녹화 표시 추가
                if self.car.data_collector:
                    frame = self.car.data_collector.draw_recording_indicator(frame)
                    frame = self.car.data_collector.draw_stats(frame)
                
                # 화면 표시
                cv2.imshow('BrainAI Car - Data Collection', frame)
                
                # 키보드 입력 처리
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print('\n프로그램 종료 요청...')
                    break
        
        except KeyboardInterrupt:
            print('\n\n프로그램 중단됨...')
        
        finally:
            self.cleanup()
    
    def _show_instructions(self):
        """조작 방법을 화면에 표시합니다."""
        print('\n' + '=' * 60)
        print('    🎮 조작 방법')
        print('=' * 60)
        print('  📍 좌측 스틱 (좌우)  → 조향 (방향 제어)')
        print('  🟢 R2 트리거         → 전진 (압력에 따라 속도 조절)')
        print('  🔴 L2 트리거         → 후진')
        print('  🔴 R1 버튼           → 녹화 시작/중지')
        print('  🗑️  L1 버튼           → 최근 10개 프레임 삭제')
        print('  ⌨️  Q 키             → 프로그램 종료')
        print('=' * 60)
        print('\n💡 팁:')
        print('  - R2를 살짝 누르면 천천히, 꽉 누르면 빠르게!')
        print('  - 도로 시작점에서 R1을 눌러 녹화를 시작하세요')
        print('  - 도로 끝에서 R1을 다시 눌러 녹화를 중지하세요')
        print('  - 잘못 저장된 데이터는 L1으로 삭제할 수 있어요')
        print('=' * 60 + '\n')
    
    def _draw_status(self, frame, fps):
        """
        프레임에 현재 상태 정보를 그립니다.
        
        Args:
            frame: 원본 비디오 프레임
            fps: 현재 FPS
            
        Returns:
            상태 정보가 추가된 프레임
        """
        height, width = frame.shape[:2]
        
        # 반투명 검은색 배경
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (480, 180), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        
        # 1. 조향 정보
        steering_text = f"Steering: {self.ps4.servo_angle}deg"
        cv2.putText(frame, steering_text, (20, 45),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # 2. 속도 정보 (색상으로 구분)
        if self.ps4.speed > 0:
            speed_text = f"Speed: FORWARD ({self.ps4.speed})"
            speed_color = (0, 255, 0)  # 초록색
        elif self.ps4.speed < 0:
            speed_text = "Speed: REVERSE"
            speed_color = (0, 0, 255)  # 빨간색
        else:
            speed_text = "Speed: STOP"
            speed_color = (200, 200, 200)  # 회색
        
        cv2.putText(frame, speed_text, (20, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, speed_color, 2)
        
        # 3. 컨트롤러 상태
        cv2.putText(frame, "PS4: CONNECTED", (20, 135),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # 4. FPS 표시
        fps_text = f"FPS: {fps:.1f}"
        cv2.putText(frame, fps_text, (20, 165),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # 5. 스티어링 휠 시각화 (오른쪽 위)
        self._draw_steering_wheel(frame, width - 110, 90)
        
        return frame
    
    def _draw_steering_wheel(self, frame, center_x, center_y):
        """
        스티어링 휠을 시각적으로 표시합니다.
        서보가 거꾸로 연결되어 있으므로 방향을 반대로 표시합니다.
        
        Args:
            frame: 프레임
            center_x: 중심 X 좌표
            center_y: 중심 Y 좌표
        """
        radius = 60
        
        # 원 그리기 (스티어링 휠)
        cv2.circle(frame, (center_x, center_y), radius, (255, 255, 255), 3)
        
        # 서보 각도를 반대로 변환 (거꾸로 연결된 서보 보정)
        inverted_angle = 180 - self.ps4.servo_angle
        
        # 현재 각도를 라디안으로 변환 (90도가 중앙)
        angle_rad = math.radians(inverted_angle - 90)
        
        # 각도 표시선의 끝점 계산
        end_x = int(center_x + radius * math.sin(angle_rad))
        end_y = int(center_y - radius * math.cos(angle_rad))
        
        # 각도 표시선 그리기 (색상: 속도에 따라 변화)
        if self.ps4.speed > 0:
            line_color = (0, 255, 0)  # 초록색 (전진)
        elif self.ps4.speed < 0:
            line_color = (0, 0, 255)  # 빨간색 (후진)
        else:
            line_color = (0, 255, 255)  # 노란색 (정지)
        
        cv2.line(frame, (center_x, center_y), (end_x, end_y), 
                line_color, 4)
        
        # 중심점 그리기
        cv2.circle(frame, (center_x, center_y), 5, line_color, -1)
    
    def cleanup(self):
        """프로그램 종료 시 리소스를 정리합니다."""
        print('\n리소스 정리 중...')
        
        # 자동차 정지 및 연결 종료
        if self.car:
            self.car.close()
        
        # PS4 컨트롤러 종료
        if self.ps4:
            self.ps4.close()
        
        print('\n프로그램이 안전하게 종료되었습니다. 👋')
        
# 버전 정보
__version__ = '1.1.0'
__author__ = 'BrainAI Co,.Ltd.'
__description__ = 'BrainAI Autonomous Driving Project - Data Collection with L1 delete support'