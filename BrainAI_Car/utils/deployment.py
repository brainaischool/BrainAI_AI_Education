"""
BrainAI Car Autonomous Driving Deployment

차선 인식 기반 자율주행 차량 제어 메인 프로그램_v1.0.0
"""

import cv2
import time
import logging
from typing import Optional

from .car_controller import BrainAICarController
from .lane_detection import LaneDetection
from .constants import (
    SERVO_CENTER,
    MOTOR_STOP,
    LATENCY_THRESHOLD,
    VIDEO_WINDOW_NAME,
    angle_to_steering
)


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BrainAICarDeployment:
    """BrainAI 자율주행 차량 배포 클래스"""

    def __init__(
        self,
        video_source: str,
        initial_speed: int = 450,
        use_serial: bool = True,
        show_messages: bool = True
    ):
        """
        Args:
            video_source: 비디오 스트림 소스 URL 또는 카메라 인덱스
            initial_speed: 초기 전진 속도 (181~1023)
            use_serial: 시리얼 통신 사용 여부
            show_messages: 디버그 메시지 표시 여부
        """
        self.video_source = video_source
        self.initial_speed = initial_speed
        self.use_serial = use_serial
        self.show_messages = show_messages

        # 컴포넌트
        self.car_controller: Optional[BrainAICarController] = None
        self.lane_detection: Optional[LaneDetection] = None
        self.video_capture: Optional[cv2.VideoCapture] = None

        # 상태 변수
        self.is_running = False
        self.is_started = False
        self.prediction_result = None
        self.latency_avg = 0.0

        logger.info("BrainAICarDeployment 초기화 완료")

    def initialize_components(self) -> bool:
        """
        모든 컴포넌트 초기화

        Returns:
            초기화 성공 여부
        """
        try:
            logger.info("컴포넌트 초기화 중...")

            # Car Controller 초기화
            self.car_controller = BrainAICarController(
                video_source=self.video_source,
                initial_speed=self.initial_speed,
                use_serial=self.use_serial,
                show_messages=self.show_messages,
                enable_recording=False  # 배포 모드에서는 녹화 비활성화
            )

            # Micro:bit 연결
            if self.use_serial:
                self.car_controller.connect_microbit()

            # Lane Detection 초기화
            self.lane_detection = LaneDetection(models_base_dir='models')

            # 비디오 캡처 초기화
            self.video_capture = cv2.VideoCapture(self.video_source)
            if not self.video_capture.isOpened():
                logger.error("비디오 스트림 열기 실패")
                return False

            logger.info("모든 컴포넌트 초기화 완료")
            return True

        except Exception as e:
            logger.error(f"컴포넌트 초기화 실패: {str(e)}")
            return False

    def process_frame(self, frame: cv2.Mat) -> None:
        """
        프레임 처리 및 차량 제어

        Args:
            frame: 입력 영상 프레임
        """
        if not self.is_started:
            return

        # 차선 인식 예측
        raw_result = self.lane_detection.predict(frame)
        self.prediction_result = self.lane_detection.postprocess(raw_result)

        # 레이턴시 업데이트
        self.latency_avg = self.lane_detection.latency

        # 조향 제어: prediction_result를 조향 값으로 변환
        # postprocess 결과는 0-100 스케일이므로 -1.0~1.0으로 변환
        steering_value = (self.prediction_result - 50.0) / 50.0
        steering_value = max(-1.0, min(1.0, steering_value))
        self.car_controller.control_steering(steering_value)

        # DC 모터 제어: 레이턴시가 낮으면 전진
        if self.latency_avg < LATENCY_THRESHOLD:
            if self.car_controller.current_motor_speed == 0:
                self.car_controller.control_speed(self.initial_speed)
        else:
            # 레이턴시가 높으면 정지
            if self.car_controller.current_motor_speed != 0:
                self.car_controller.control_speed(0)

    def draw_overlay(self, frame: cv2.Mat) -> cv2.Mat:
        """
        프레임에 오버레이 정보 표시

        Args:
            frame: 입력 프레임

        Returns:
            오버레이가 그려진 프레임
        """
        overlay = frame.copy()
        height, width = frame.shape[:2]

        # 반투명 배경
        cv2.rectangle(
            overlay,
            (10, 10),
            (width - 10, 150),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

        # 상태 정보
        y_offset = 35
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2

        # 자율주행 상태
        status = "BrainAI Car Autonomous Driving: ON" if self.is_started else "Driving: OFF"
        status_color = (0, 255, 0) if self.is_started else (128, 128, 128)
        cv2.putText(
            frame,
            status,
            (20, y_offset),
            font,
            font_scale,
            status_color,
            thickness
        )
        y_offset += 35

        if self.is_started and self.prediction_result is not None:
            # 현재 모델
            cv2.putText(
                frame,
                f"Model: {self.lane_detection.current_model}",
                (20, y_offset),
                font,
                font_scale,
                (0, 255, 255),
                thickness
            )
            y_offset += 35

            # 조향 정보
            steering_text = f"Steering: {self.car_controller.current_servo_angle}"
            cv2.putText(
                frame,
                steering_text,
                (20, y_offset),
                font,
                font_scale,
                (255, 255, 0),
                thickness
            )
            y_offset += 35

            # 레이턴시
            latency_ms = self.latency_avg * 1000
            cv2.putText(
                frame,
                f"Latency: {latency_ms:.1f}ms",
                (20, y_offset),
                font,
                font_scale,
                (255, 100, 100),
                thickness
            )

        return frame

    def handle_keyboard_input(self, key: int) -> bool:
        """
        키보드 입력 처리

        Args:
            key: 입력된 키 값

        Returns:
            프로그램 종료 여부 (True: 종료)
        """
        if key == ord('q'):
            logger.info("종료 키 입력 감지")
            return True

        elif key == ord('s'):
            self.is_started = not self.is_started
            state = "시작" if self.is_started else "정지"
            logger.info(f"자율주행 {state}")

            if not self.is_started:
                # 정지 시 차량 멈춤
                self.car_controller.control_speed(0)

        elif key == ord('1'):
            logger.info("모델 전환: laneD1")
            self.lane_detection.switch_model("laneD1", manual_override=True)

        elif key == ord('2'):
            logger.info("모델 전환: laneD2")
            self.lane_detection.switch_model("laneD2", manual_override=True)

        return False

    def run(self) -> None:
        """메인 실행 루프"""
        logger.info("=" * 60)
        logger.info("BrainAI Car 자율주행 시스템 시작")
        logger.info("=" * 60)
        logger.info("조작 키:")
        logger.info("  Q: 종료")
        logger.info("  S: 시작/정지")
        logger.info("  1: laneD1 모델 전환")
        logger.info("  2: laneD2 모델 전환")
        logger.info("=" * 60)

        if not self.initialize_components():
            self.cleanup()
            return

        self.is_running = True

        try:
            while self.is_running:
                # 프레임 읽기
                ret, frame = self.video_capture.read()
                if not ret:
                    logger.warning("프레임 읽기 실패")
                    time.sleep(0.01)
                    continue

                # 프레임 처리
                self.process_frame(frame)

                # 모델 자동 전환 타임아웃 확인
                self.lane_detection.check_switch_timeout()

                # 오버레이 그리기
                frame = self.draw_overlay(frame)

                # 화면 출력
                cv2.imshow(VIDEO_WINDOW_NAME, frame)

                # 키보드 입력 처리
                key = cv2.waitKey(1) & 0xFF
                if self.handle_keyboard_input(key):
                    break

        except KeyboardInterrupt:
            logger.info("Ctrl+C 감지 - 프로그램 종료 중...")

        except Exception as e:
            logger.error(f"실행 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """리소스 정리"""
        logger.info("리소스 정리 중...")

        if self.video_capture is not None:
            self.video_capture.release()
            logger.info("✓ 비디오 캡처 해제")

        cv2.destroyAllWindows()

        if self.car_controller is not None:
            self.car_controller.close()

        logger.info("=" * 60)
        logger.info("BrainAI Car 자율주행 시스템 종료")
        logger.info("=" * 60)


# 버전 정보
__version__ = '1.0.0'
__author__ = 'BrainAI Co,.Ltd.'
__description__ = 'BrainAI Autonomous Driving Deployment - car_controller based'