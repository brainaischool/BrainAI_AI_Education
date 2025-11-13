"""
BrainAI Car [PS4 컨트롤러] 모듈_v1.1.0
PS4 컨트롤러 입력을 받아서 BrainAI Car를 제어합니다.

모듈 위치: utils/ 
모듈 이름: ps4_controller.py

변경사항 v1.1.0:
- L1 버튼으로 최근 10개 프레임/어노테이션 삭제 기능 추가
"""

import pygame
from .constants import steering_to_angle


# PS4 컨트롤러 버튼 매핑 상수 (pygame 표준 매핑)
BUTTON_R1 = 10         # R1 버튼 (녹화용)
BUTTON_L1 = 9          # L1 버튼 (삭제용)

# 축(Axis) 매핑
AXIS_LEFT_STICK_X = 0   # 좌측 스틱 좌우
AXIS_L2_TRIGGER = 4     # L2 트리거
AXIS_R2_TRIGGER = 5     # R2 트리거


class PS4Controller:
    """PS4 컨트롤러 입력을 처리하는 클래스"""
    
    def __init__(self, car=None):
        """
        PS4 컨트롤러 초기화
        
        Args:
            car: BrainAICarController 객체
        """
        # pygame 초기화
        pygame.init()
        pygame.joystick.init()
        
        self.car = car
        self.controller = None
        self.connected = False
        
        # 컨트롤러 연결 확인
        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            self.connected = True
            print("✓ PS4 컨트롤러 연결됨")
            print("  - R1: 녹화 시작/중지")
            print("  - L1: 최근 10개 프레임 삭제")
        else:
            print("✗ PS4 컨트롤러를 찾을 수 없습니다")
        
        # 현재 상태 저장 변수
        self.servo_angle = 90  # 현재 서보 각도
        self.speed = 0         # 현재 속도
        
        # 아날로그 속도 제어용
        self.min_speed = 200   # 최소 전진 속도
        self.max_speed = 1023  # 최대 전진 속도
        
        # 버튼 상태 추적 (토글용)
        self.r1_was_pressed = False
        self.l1_was_pressed = False  # 🆕 L1 버튼 상태
    
    def get_steering(self):
        """
        조향 값을 가져옵니다.
        
        Returns:
            float: -1.0(왼쪽) ~ 0(중앙) ~ 1.0(오른쪽)
        """
        if not self.connected:
            return 0.0
        
        # 좌측 스틱의 X축 값
        steering = self.controller.get_axis(AXIS_LEFT_STICK_X)
        
        # 데드존 적용 (미세한 흔들림 제거)
        if abs(steering) < 0.1:
            steering = 0.0
        
        return steering
    
    def get_trigger_value(self, trigger_axis):
        """
        트리거 값을 가져옵니다 (0.0 ~ 1.0)
        
        Args:
            trigger_axis: 트리거 축 번호
            - AXIS_L2_TRIGGER: L2 트리거
            - AXIS_R2_TRIGGER: R2 트리거
        
        Returns:
            float: 0.0(안 누름) ~ 1.0(완전히 누름)
        """
            
        if not self.connected:
            return 0.0
        
        # PS4 트리거는 -1.0~1.0 범위이므로 0.0~1.0으로 변환
        raw_value = self.controller.get_axis(trigger_axis)
        return (raw_value + 1.0) / 2.0
    
    def is_r1_pressed(self):
        """
        R1 버튼이 눌렸는지 확인 (토글 방식)
        
        Returns:
            bool: 버튼이 방금 눌렸으면 True
        """
        if not self.connected:
            return False
        
        current_state = self.controller.get_button(BUTTON_R1)
        
        # 버튼이 눌린 순간 감지 (이전: 안눌림 → 현재: 눌림)
        if current_state and not self.r1_was_pressed:
            self.r1_was_pressed = True
            return True
        elif not current_state:
            self.r1_was_pressed = False
        
        return False
    
    def is_l1_pressed(self):
        """
        L1 버튼이 눌렸는지 확인 (토글 방식)
        
        Returns:
            bool: 버튼이 방금 눌렸으면 True
        """
        if not self.connected:
            return False
        
        current_state = self.controller.get_button(BUTTON_L1)
        
        # 버튼이 눌린 순간 감지 (이전: 안눌림 → 현재: 눌림)
        if current_state and not self.l1_was_pressed:
            self.l1_was_pressed = True
            return True
        elif not current_state:
            self.l1_was_pressed = False
        
        return False
    
    def process_events(self, frame=None):
        """
        컨트롤러 입력을 처리하고 자동차를 제어합니다.
        반복문 안에서 계속 호출해야 합니다.
        
        Args:
            frame: 현재 프레임 (녹화용, 선택사항)
        """
        # pygame 이벤트 업데이트
        pygame.event.pump()
        
        if not self.connected or not self.car:
            return
        
        # R1 버튼 처리 (녹화 토글)
        if self.is_r1_pressed():
            if frame is not None:
                self.car.toggle_recording(frame)
            else:
                print("⚠ 녹화하려면 프레임이 필요합니다")
        
        # L1 버튼 처리 (삭제)
        if self.is_l1_pressed():
            self.car.delete_last_frames(10)
        
        # 1. 조향 처리 (좌측 스틱)
        steering = self.get_steering()

        # 조향 값을 서보 각도로 변환
        new_angle = steering_to_angle(steering)
        
        # 각도가 변경되었을 때만 전송
        if abs(new_angle - self.servo_angle) > 1:
            self.servo_angle = new_angle
            self.car.control_steering(steering)
        
        # 2. 속도 처리 (R2, L2 트리거)
        r2_value = self.get_trigger_value(AXIS_R2_TRIGGER)  # R2 (전진)
        l2_value = self.get_trigger_value(AXIS_L2_TRIGGER)  # L2 (후진)  
        new_speed = 0  # 기본: 정지
        
        # R2를 누르면 전진 (아날로그 속도 제어)
        if r2_value > 0.1:  # 데드존
            # 트리거 값(0.0~1.0)을 속도(min_speed~max_speed)로 매핑
            speed_range = self.max_speed - self.min_speed
            new_speed = int(self.min_speed + (speed_range * r2_value))
            new_speed = max(self.min_speed, min(self.max_speed, new_speed))
        
        # L2를 누르면 후진 (우선순위 높음)
        elif l2_value > 0.1:
            new_speed = -1  # 마이크로비트가 -1을 후진으로 인식
        
        # 속도가 변경되었을 때만 전송
        if new_speed != self.speed:
            self.speed = new_speed
            self.car.control_speed(self.speed)
    
    def close(self):
        """pygame 리소스를 정리합니다."""
        pygame.quit()
        print("PS4 컨트롤러 연결 종료")

        
# 버전 정보
__version__ = '1.1.0'
__author__ = 'BrainAI Co,.Ltd.'
__description__ = 'BrainAI Autonomous Driving Project - L1 button for deleting last 10 frames'