"""
PS4 컨트롤러 매핑 모듈
BrainAI Car 조정을 위한 PS4 컨트롤러 클래스

이 모듈은 PS4 컨트롤러의 버튼, 트리거, 스틱을 테스트하는 기능을 제공합니다.
"""

import pygame
import time
import os


class PS4ControllerConnector:
    """PS4 컨트롤러를 관리하는 클래스"""
    
    # 버튼 이름 매핑
    BUTTON_NAMES = {
        0: "X (크로스)",
        1: "O (원)",
        2: "□ (사각형)",
        3: "△ (삼각형)",
        4: "Share",
        5: "PS 버튼",
        6: "Options",
        7: "좌 스틱 버튼",
        8: "우 스틱 버튼",
        9: "L1",
        10: "R1",
        11: "↑ (위 방향키)",
        12: "↓ (아래 방향키)",
        13: "← (왼쪽 방향키)",
        14: "→ (오른쪽 방향키)"
    }
    
    # 축 이름 매핑
    AXIS_NAMES = {
        0: "좌 스틱 X축 (좌우)",
        1: "좌 스틱 Y축 (위아래)",
        2: "우 스틱 X축 (좌우)",
        3: "우 스틱 Y축 (위아래)",
        4: "L2 트리거",
        5: "R2 트리거"
    }
    
    def __init__(self):
        """컨트롤러 초기화"""
        pygame.init()
        pygame.joystick.init()
        self.controller = None
        self.deadzone = 0.1
        
    def connect(self):
        """컨트롤러 연결 시도"""
        if pygame.joystick.get_count() == 0:
            return False
        
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()
        return True
    
    def get_info(self):
        """컨트롤러 정보 반환"""
        if not self.controller:
            return None
        
        return {
            'name': self.controller.get_name(),
            'num_buttons': self.controller.get_numbuttons(),
            'num_axes': self.controller.get_numaxes()
        }
    
    def apply_deadzone(self, value, threshold=None):
        """데드존 적용 - 작은 값은 0으로 처리"""
        if threshold is None:
            threshold = self.deadzone
        
        if abs(value) < threshold:
            return 0.0
        return value
    
    def get_button(self, button_id):
        """특정 버튼의 상태 반환"""
        pygame.event.pump()
        return self.controller.get_button(button_id)
    
    def get_all_buttons(self):
        """모든 버튼의 상태 반환"""
        pygame.event.pump()
        pressed = []
        for i in range(self.controller.get_numbuttons()):
            if self.controller.get_button(i):
                pressed.append(i)
        return pressed
    
    def get_axis(self, axis_id):
        """특정 축의 값 반환 (데드존 적용)"""
        pygame.event.pump()
        value = self.controller.get_axis(axis_id)
        return self.apply_deadzone(value)
    
    def get_all_axes(self):
        """모든 축의 값 반환 (데드존 적용)"""
        pygame.event.pump()
        values = []
        for i in range(self.controller.get_numaxes()):
            value = self.controller.get_axis(i)
            values.append(self.apply_deadzone(value))
        return values
    
    def close(self):
        """컨트롤러 연결 종료"""
        pygame.quit()


class PS4ControllerTester:
    """PS4 컨트롤러 테스트 클래스"""
    
    def __init__(self, controller):
        """테스터 초기화"""
        self.controller = controller
    
    @staticmethod
    def clear_screen():
        """화면 지우기 (OS별 처리)"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def test_buttons(self):
        """버튼 테스트 모드"""
        print("\n" + "="*70)
        print("  🎮 버튼 테스트 모드")
        print("="*70)
        print("모든 버튼을 눌러보세요! (Ctrl+C로 종료)\n")
        
        last_states = [False] * 20
        
        try:
            while True:
                pygame.event.pump()
                
                # 모든 버튼 확인
                for i in range(self.controller.controller.get_numbuttons()):
                    current = self.controller.get_button(i)
                    
                    # 버튼이 눌렸을 때
                    if current and not last_states[i]:
                        button_name = PS4Controller.BUTTON_NAMES.get(i, "알 수 없음")
                        print(f"✓ 버튼 {i:2d} 눌림 - {button_name}")
                        
                        # R1 버튼 강조
                        if i == 10:
                            print("  " + "="*60)
                            print(f"  ⭐ 이것이 R1 버튼입니다! (녹화 버튼)")
                            print("  " + "="*60)
                    
                    last_states[i] = current
                
                time.sleep(0.05)
        
        except KeyboardInterrupt:
            print("\n\n버튼 테스트 종료")
    
    def test_axes(self):
        """축(Axis) 테스트 모드"""
        self.clear_screen()
        
        print("="*70)
        print("  🕹️  축(Axis) 테스트 모드")
        print("="*70)
        print()
        print("좌/우 스틱을 움직이고 L2/R2 트리거를 당겨보세요!")
        print("Ctrl+C로 종료")
        print("="*70)
        print()
        
        # 이전 값 저장 (변화 감지용)
        prev_values = [0.0] * 10
        
        try:
            line_count = self.controller.controller.get_numaxes()
            first_run = True
            
            while True:
                pygame.event.pump()
                time.sleep(0.1)
                
                # 변화 감지
                has_change = False
                current_values = self.controller.get_all_axes()
                
                for i in range(len(current_values)):
                    # 0.05 이상 변화가 있으면 갱신
                    if abs(current_values[i] - prev_values[i]) > 0.05:
                        has_change = True
                
                # 변화가 있을 때만 화면 갱신
                if has_change or first_run:
                    # 첫 실행이 아니면 커서를 위로 올려서 덮어쓰기
                    if not first_run:
                        print("\033[F" * line_count, end='')
                    
                    for i in range(len(current_values)):
                        value = current_values[i]
                        
                        # 값 시각화 (바 그래프)
                        bar_length = 30
                        normalized = (value + 1.0) / 2.0
                        filled = int(normalized * bar_length)
                        bar = "█" * filled + "░" * (bar_length - filled)
                        
                        # 축 레이블
                        axis_label = PS4Controller.AXIS_NAMES.get(i, f"축 {i}")
                        
                        # 한 줄로 출력: 축 번호 + 레이블 | 바 | 값
                        # 줄 전체를 지우고 새로 쓰기
                        print(f"\r\033[K축 {i}: {axis_label:25s} | [{bar}] {value:+.3f}")
                    
                    prev_values = current_values[:]
                    first_run = False
                
        except KeyboardInterrupt:
            print("\n\n축 테스트 종료")
    
    def test_realtime(self):
        """실시간 모니터링 모드"""
        self.clear_screen()
        
        print("="*70)
        print("  📊 실시간 모니터링 모드")
        print("="*70)
        print()
        print("모든 입력을 실시간으로 확인합니다!")
        print("Ctrl+C로 종료")
        print("="*70)
        print()
        
        # 이전 상태 저장
        prev_buttons = set()
        prev_axes = [0.0] * 10
        
        # 초기 화면 출력
        for _ in range(15):
            print()
        
        try:
            while True:
                pygame.event.pump()
                time.sleep(0.1)
                
                # 현재 상태 수집
                current_buttons = set(self.controller.get_all_buttons())
                current_axes = self.controller.get_all_axes()
                
                # 변화 감지
                buttons_changed = current_buttons != prev_buttons
                axes_changed = any(abs(current_axes[i] - prev_axes[i]) > 0.05 
                                 for i in range(len(current_axes)))
                
                # 변화가 있을 때만 갱신
                if buttons_changed or axes_changed:
                    # 화면 갱신 (덮어쓰기)
                    print("\033[F" * 15)
                    
                    # 버튼 상태
                    print("🎮 버튼 상태:")
                    print("-" * 70)
                    
                    if current_buttons:
                        button_list = []
                        for btn_id in sorted(current_buttons):
                            btn_name = PS4Controller.BUTTON_NAMES.get(btn_id, "알 수 없음")
                            button_list.append(f"{btn_id} 눌림 - {btn_name}")
                        print(f"\r\033[K  눌린 버튼: {', '.join(button_list)}")
                    else:
                        print("\r\033[K  눌린 버튼: 없음")
                    
                    print()
                    
                    # 축 상태
                    print("🕹️  축(Axis) 상태:")
                    print("-" * 70)
                    
                    # 좌 스틱
                    if len(current_axes) > 1:
                        lx = current_axes[0]
                        ly = current_axes[1]
                        print(f"  좌 스틱   - X: {lx:+.3f}  Y: {ly:+.3f}")
                    
                    # 우 스틱
                    if len(current_axes) > 3:
                        rx = current_axes[2]
                        ry = current_axes[3]
                        print(f"  우 스틱   - X: {rx:+.3f}  Y: {ry:+.3f}")
                    elif len(current_axes) > 2:
                        rx = current_axes[2]
                        print(f"  우 스틱   - X: {rx:+.3f}")
                    
                    print()
                    
                    # 트리거
                    if len(current_axes) > 4:
                        # L2 (축 4)
                        l2_raw = current_axes[4]
                        l2 = (l2_raw + 1.0) / 2.0
                        l2_bar = "█" * int(l2 * 20) + "░" * (20 - int(l2 * 20))
                        print(f"  L2 트리거 - [{l2_bar}] {l2:.3f}")
                        
                        # R2 (축 5)
                        if len(current_axes) > 5:
                            r2_raw = current_axes[5]
                            r2 = (r2_raw + 1.0) / 2.0
                            r2_bar = "█" * int(r2 * 20) + "░" * (20 - int(r2 * 20))
                            print(f"  R2 트리거 - [{r2_bar}] {r2:.3f}")
                    
                    print("-" * 70)
                    print()
                    print()
                    
                    # 상태 저장
                    prev_buttons = current_buttons
                    prev_axes = current_axes[:]
                
        except KeyboardInterrupt:
            print("\n\n모니터링 종료")


# 버전 정보
__version = 'BrainAI_Car_2025.1.0.0'
__author = 'BrainAI Co,.Ltd.'
__description = 'BrainAI Autonomous Driving Project - PS4 Mapping Module'