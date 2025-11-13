"""
BrainAI Car [BrainAI car 컨트롤러] 모듈_v1.0.0
PS4 컨트롤러 입력을 받아서 BrainAI Car를 제어하고 R1 버튼으로 녹화를 제어합니다.

모듈 위치: utils/ 
모듈 이름: car_controller.py

"""

import time
import threading

import cv2
import serial
import serial.tools.list_ports

from .constants import (
    SERVO_CENTER,
    MOTOR_STOP,
    SPEED_DEFAULT
)

from .data_collector import DataCollector

class BrainAICarController:
    """BrainAI Car 제어 클래스 (PS4 컨트롤러 전용 - 실시간 제어)"""

    def __init__(self, video_source=0, initial_speed=SPEED_DEFAULT,
                 use_serial=True, show_messages=True,
                 enable_recording=False):
        """
        BrainAI Car 컨트롤러 초기화

        Args:
            video_source (int or str): 비디오 소스
            initial_speed (int): 초기 속도 (181~1023)
            use_serial (bool): 시리얼 통신 사용 여부
            show_messages (bool): 디버그 메시지 표시 여부
            enable_recording (bool) : 녹화 기능 활성화
        """
        self.video_source = video_source
        self.forward_speed = initial_speed
        self.use_serial = use_serial
        self.show_messages = show_messages
        self.serial_port = None
        self.video_capture = None

        # 현재 상태
        self.current_servo_angle = SERVO_CENTER
        self.current_motor_speed = MOTOR_STOP

        # 재시도 시스템 (모터만)
        self.serial_interval = 0.05  # 최소 전송 간격
        self.last_serial_send_time = time.time()

        # 강제 정지 로직
        self.stop_start_time = None
        self.minimum_stop_duration = 0.5
        self.is_in_forced_stop = False

        # 시리얼 읽기 스레드
        self.reading_thread = None
        self.stop_reading = False
        
        # 데이터 획득기 추가
        self.enable_recording = enable_recording
        self.data_collector = None
        
        if self.enable_recording:
            from pathlib import Path
            data_path = Path(__file__).parent.parent / "data_laneD1"
            self.data_collector = DataCollector(
                video_prefix="brainai_car",
                save_fps=12,
                data_dir=str(data_path)
            )
        self.serial_lock = threading.Lock()
        
    def connect_microbit(self):
        """마이크로비트 연결"""
        if not self.use_serial:
            return
        
        if self.show_messages:
            print('\n-- Micro:bit 연결 중 --')
             
        
        ports = serial.tools.list_ports.comports()
        
        for port, desc, hwid in sorted(ports):
            if 'USB' in desc:
                try:
                    if self.show_messages:
                        print(f'Micro:bit 감지: {port}')
                    
                    # 기존 연결 닫기
                    if self.serial_port and self.serial_port.is_open:
                        self.serial_port.close()
                    
                    self.serial_port = serial.Serial(
                        port, 
                        115200, 
                        timeout=0.1,
                        parity=serial.PARITY_NONE,
                        rtscts=0
                    )
                    
                    # 버퍼 초기화
                    self.serial_port.reset_input_buffer()
                    self.serial_port.reset_output_buffer()
                    time.sleep(0.1)
                    
                    # 읽기 스레드 시작
                    self.start_serial_reading()
                    
                    # 초기화 명령: 서보 중앙, 모터 정지
                    self.send_command_internal(SERVO_CENTER, bypass_rate_limit=True)
                    time.sleep(0.05)
                    self.send_command_internal(MOTOR_STOP, bypass_rate_limit=True)
                    time.sleep(0.05)

                    # 현재 상태 업데이트
                    self.current_servo_angle = SERVO_CENTER
                    self.current_motor_speed = MOTOR_STOP
                    
                    if self.show_messages:
                        print('✓ Micro:bit 연결 성공')
                    return
                    
                except serial.SerialException as e:
                    if self.show_messages:
                        print(f'✗ 포트 열기 실패: {e}')
                    continue
        
        if self.show_messages:
            print('\n' + '='*60)
            print('❌ Micro:bit을 찾을 수 없습니다')
            print('='*60)
            print('\n해결 방법:')
            print('  1. USB 케이블이 연결되어 있는지 확인하세요')
            print('  2. Micro:bit에 펌웨어가 업로드되어 있는지 확인하세요')
            print('  3. 장치 관리자에서 COM 포트가 인식되는지 확인하세요')
            print('  4. USB 케이블을 다시 연결해보세요')
            print('='*60 + '\n')
    
    def start_serial_reading(self):
        """시리얼 읽기 스레드 시작"""
        if self.serial_port and not self.reading_thread:
            self.stop_reading = False
            self.reading_thread = threading.Thread(target=self._read_serial_continuously)
            self.reading_thread.daemon = True
            self.reading_thread.start()
                
    def _read_serial_continuously(self):
        """시리얼 데이터 지속적으로 읽기"""
        while not self.stop_reading:
            try:
                with self.serial_lock:  # ← 락 안에서 모든 작업
                    if not self.serial_port or not self.serial_port.is_open:
                        break
                    
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.readline().decode('utf-8').strip()
                        if data and self.show_messages:
                            print(f'[마이크로비트] {data}')
            except Exception as e:
                if self.show_messages:
                    print(f'시리얼 읽기 오류: {e}')
                break
            
            time.sleep(0.001)
                    
    def send_command_internal(self, command, bypass_rate_limit=False):
        """
        내부 명령 전송
        
        Args:
            command (int): 전송할 명령 값
            bypass_rate_limit (bool): 속도 제한 우회
        
        Returns:
            bool: 전송 성공 여부
        """
        if not self.use_serial:
            return False
        
        # 시리얼 포트 상태 확인
        with self.serial_lock:
            if not self.serial_port or not self.serial_port.is_open:
                return False
            
            current_time = time.time()
            
            # 속도 제한 (서보는 제외, bypass_rate_limit가 True면 무시)
            if not bypass_rate_limit and (current_time - self.last_serial_send_time) < self.serial_interval:
                if not (35 <= command <= 145):  # 서보 범위 외
                    return False
            
            try:
                self.serial_port.write(f"{command}\n".encode())
                self.serial_port.flush()
                time.sleep(0.01)
                self.last_serial_send_time = current_time
                return True
            except serial.SerialException as e:
                if self.show_messages:
                    print(f'✗ 명령 전송 실패: {e}')
                return False
                
    def control_steering(self, steering_value):
        """
        조향 제어 (PS4용)
        
        Args:
            steering_value (float): -1.0(왼쪽) ~ 0(중앙) ~ 1.0(오른쪽)
        """
        # 각도 계산
        angle = 90 - int(steering_value * 45)
        angle = max(45, min(135, angle))
        
        # 즉시 전송 (재시도 없음)
        self.set_servo_angle(angle)
    
    def control_speed(self, speed):
        """
        속도 제어 (PS4용)
        
        Args:
            speed (int): 모터 속도 (0, -1, 또는 181~1023)
        """
        # 즉시 전송 (확인 없음)
        self.set_motor_speed_immediate(speed)
    
    def set_servo_angle(self, angle):
        """
        서보 각도 설정
        
        Args:
            angle (int): 서보 각도 (45~135)
        """
        if not (45 <= angle <= 135):
            return
        
        # 현재 각도 업데이트
        self.current_servo_angle = angle
        self.send_command_internal(angle, bypass_rate_limit=False)
    
    def set_motor_speed_immediate(self, speed):
        """
        모터 속도 즉시 설정
        
        Args:
            speed (int): 0(정지), -1(후진), 181~1023(전진)
        """
        # 현재 속도 업데이트
        self.current_motor_speed = speed
        self.send_command_internal(speed, bypass_rate_limit=True)
        
    def set_forward_speed(self, speed):
        """
        전진 기본 속도 설정
        
        Args:
            speed (int): 전진 속도 (181~1023)
        """
        self.forward_speed = max(181, min(1023, speed))
        if self.show_messages:
            print(f'전진 속도 설정: {self.forward_speed}')
            
    def toggle_recording(self, frame):
        """녹화 시작/중지 토글"""
        if not self.enable_recording or not self.data_collector:
            return
        
        if self.data_collector.recording:
            self.data_collector.stop_recording()
        else:
            self.data_collector.start_recording(frame)
    
    def delete_last_frames(self, count=10):
        """
        최근 프레임과 어노테이션 삭제
        
        Args:
            count (int): 삭제할 프레임 수 (기본값: 10)
        """
        if not self.enable_recording or not self.data_collector:
            print("⚠ 녹화 기능이 활성화되지 않았습니다.")
            return
        
        self.data_collector.delete_last_files(count)
            
    def save_data_frame(self, frame):
        """현재 프레임과 조향 데이터 저장"""
        if self.enable_recording and self.data_collector and self.data_collector.recording:
            self.data_collector.save_frame(
                frame, 
                self.current_servo_angle,
                self.current_motor_speed
            )
    
    def close(self):
        if self.show_messages:
            print('\n리소스 정리 중...')
        
        # 안전 정지: 여러 번 시도
        if self.serial_port and self.serial_port.is_open:
            print('차량 정지 중...')
            
            # 3번 시도
            for attempt in range(3):
                success = self.send_command_internal(MOTOR_STOP, bypass_rate_limit=True)
                if success:
                    time.sleep(0.05)
                    # 서보도 중앙으로
                    self.send_command_internal(SERVO_CENTER, bypass_rate_limit=True)
                    time.sleep(0.05)
                    break
                else:
                    print(f'  재시도 {attempt + 1}/3...')
                    time.sleep(0.1)
            
            if self.show_messages:
                print('✓ 차량 정지 완료')
        
            # 읽기 스레드 중지
            self.stop_reading = True
            if self.reading_thread:
                self.reading_thread.join(timeout=1.0)
            
            # 시리얼 포트 닫기
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                if self.show_messages:
                    print('✓ 시리얼 포트 닫힘')
            
            # 비디오 해제
            if self.video_capture:
                self.video_capture.release()
                if self.show_messages:
                    print('✓ 카메라 해제됨')
            
            cv2.destroyAllWindows()
            if self.show_messages:
                print('✓ 프로그램 종료\n')
                
            # 데이터 획득기 정리
            if self.data_collector:
                self.data_collector.cleanup()  

# 버전 정보
__version__ = '1.0.0'
__author__ = 'BrainAI Co,.Ltd.'
__description__ = 'BrainAI Autonomous Driving Project - No retry for real-time control'