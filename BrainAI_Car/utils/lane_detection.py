"""
Lane Detection Module

OpenVINO 기반 차선 인식 모델 로드 및 추론 모듈
"""

import os
import time
import logging
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from openvino import Core


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LaneDetection:
    """차선 인식 클래스 (OpenVINO 기반)"""

    def __init__(
        self,
        models_base_dir: str = 'models',
        video_stream: Optional[object] = None
    ):
        """
        Args:
            models_base_dir: 모델 디렉토리 경로
            video_stream: 비디오 스트림 객체 (선택)
        """
        self.models_base_dir = models_base_dir
        self.video_stream = video_stream

        # 모델 경로 설정
        self.model_paths = {
            "laneD1": os.path.join(models_base_dir, 'laneD1', 'laneD1.xml'),
            "laneD2": os.path.join(models_base_dir, 'laneD2', 'laneD2.xml'),
        }

        # 모델 관리
        self.models: Dict = {}
        self.model_configs: Dict = {}
        self.current_model_name: str = "laneD1"

        # 모델 전환 관리
        self.switch_time: float = time.time()
        self.switch_duration: float = 7.0
        self.last_direction_model: Optional[str] = None

        # 방향 확인 추적
        self.switch_requests: Dict[str, int] = {}
        self.confirmation_count: int = 3

        # 레이턴시 추적 (최근 20 프레임 평균)
        self.latency_history: np.ndarray = np.zeros(20)
        self.latency_idx: int = 0
        self.total_predictions: int = 0

        # 모델 로드
        self.load_models()
        logger.info("LaneDetection 초기화 완료")

    def load_models(self) -> None:
        """모든 사용 가능한 모델 로드"""
        logger.info("=" * 60)
        logger.info("자율주행 모델 로드 중...")
        logger.info("=" * 60)

        available_models = []
        core = Core()

        for model_name, model_path in self.model_paths.items():
            if not os.path.exists(model_path):
                logger.warning(f"모델 파일 없음: {model_path} - {model_name} 건너뜀")
                continue

            try:
                # 모델 로드 및 컴파일
                model = core.read_model(model_path)
                compiled_model = core.compile_model(model, "CPU")

                # 모델 설정 가져오기
                output_layer = compiled_model.output(0)
                input_layer = compiled_model.input(0)

                # 입력 shape 파싱
                input_shape = []
                for dim in input_layer.partial_shape:
                    input_shape.append(
                        1 if dim.is_dynamic else dim.get_length()
                    )
                n, input_height, input_width, c = input_shape

                # 모델 및 설정 저장
                self.models[model_name] = compiled_model
                self.model_configs[model_name] = {
                    'output_layer': output_layer,
                    'input_width': input_width,
                    'input_height': input_height
                }

                available_models.append(model_name)
                logger.info(f"✓ {model_name} 로드 완료: {model_path}")

            except Exception as e:
                logger.error(f"✗ {model_name} 로드 실패: {str(e)}")

        # 최소 1개 모델 확인
        if not self.models:
            raise RuntimeError("차선 인식 모델을 로드할 수 없습니다!")

        # 기본 모델이 없으면 첫 번째 모델 사용
        if self.current_model_name not in self.models:
            self.current_model_name = list(self.models.keys())[0]
            logger.warning(
                f"기본 모델 없음 - {self.current_model_name} 사용"
            )

        logger.info(f"현재 활성 모델: {self.current_model_name}")
        logger.info("=" * 60)

    def preprocess(self, img: np.ndarray) -> np.ndarray:
        """
        이미지 전처리 (학습 파이프라인과 동일)

        Args:
            img: 입력 이미지

        Returns:
            전처리된 이미지 (배치 차원 포함)
        """
        config = self.model_configs[self.current_model_name]

        # 1단계: 모델 입력 크기로 리사이즈
        img_resized = cv2.resize(
            img,
            (config['input_width'], config['input_height'])
        )

        # 2단계: [0, 1]로 정규화
        img_normalized = img_resized.astype(np.float32) / 255.0

        # 3단계: 상단 절반 제거 (학습과 동일)
        half_height = config['input_height'] // 2
        img_normalized[:half_height, :, :] = 0.0

        # 4단계: [-1, 1] 범위로 스케일링
        img_normalized = img_normalized * 2.0 - 1.0

        # 5단계: 배치 차원 추가
        img_expand = np.expand_dims(img_normalized, axis=0)

        return img_expand

    def predict(self, img: np.ndarray) -> float:
        """
        차선 인식 예측 수행

        Args:
            img: 입력 이미지

        Returns:
            예측 결과 (raw output)
        """
        # 예측 시작 시간
        start_time = time.perf_counter()

        # 현재 모델 및 설정
        current_model = self.get_current_model()
        config = self.model_configs[self.current_model_name]

        # 이미지 전처리
        input_image = self.preprocess(img)

        # 추론 실행
        raw_result = current_model([input_image])[config['output_layer']][0]

        # 예측 종료 시간 및 레이턴시 기록
        end_time = time.perf_counter()
        frame_latency = end_time - start_time

        # 레이턴시 히스토리 업데이트
        self.latency_history[self.latency_idx] = frame_latency
        self.latency_idx = (self.latency_idx + 1) % 20
        self.total_predictions += 1

        # Raw 결과 반환
        return raw_result

    def postprocess(self, result: float) -> float:
        """
        모델 출력을 조향 값으로 변환 (0-100 스케일)

        Args:
            result: 모델 raw output

        Returns:
            정규화된 조향 값
        """
        normalized_result = (result + 1.0) * 50.0
        return normalized_result

    def get_current_model(self):
        """
        현재 활성 모델 반환

        Returns:
            컴파일된 OpenVINO 모델

        Raises:
            RuntimeError: 사용 가능한 모델이 없을 때
        """
        if self.current_model_name in self.models:
            return self.models[self.current_model_name]

        # 첫 번째 사용 가능한 모델로 폴백
        available_models = list(self.models.keys())
        if available_models:
            self.current_model_name = available_models[0]
            logger.warning(
                f"현재 모델 없음 - {self.current_model_name}로 전환"
            )
            return self.models[self.current_model_name]

        raise RuntimeError("사용 가능한 차선 인식 모델이 없습니다!")

    def set_switch_duration(self, duration: float) -> None:
        """
        모델 전환 지속 시간 설정

        Args:
            duration: 지속 시간 (초)
        """
        self.switch_duration = duration
        logger.info(f"모델 전환 지속 시간 설정: {duration}초")

    def switch_model(
        self,
        model_name: str,
        manual_override: bool = False
    ) -> bool:
        """
        모델 전환

        Args:
            model_name: 전환할 모델 이름
            manual_override: 수동 전환 여부 (키 입력)

        Returns:
            전환 성공 여부
        """
        if model_name not in self.models:
            logger.warning(
                f"모델 {model_name} 없음 - "
                f"현재 모델 {self.current_model_name} 유지"
            )
            return False

        current_time = time.time()

        # 수동 전환 (키 입력)
        if manual_override:
            if model_name != self.current_model_name:
                self.current_model_name = model_name
                self.switch_time = current_time

                # 방향 기반 모델 추적
                if model_name in ["laneD2"]:
                    self.last_direction_model = model_name
                elif model_name == "laneD1":
                    self.last_direction_model = None

                # 전환 요청 카운터 리셋
                self.switch_requests = {}
                logger.info(f"수동 전환: {model_name}")
                return True
            else:
                # 동일 모델 - 타이머만 갱신
                self.switch_time = current_time
                return True

        # 자동 전환 (방향 감지) - 확인 필요
        if model_name not in self.switch_requests:
            self.switch_requests[model_name] = 0

        # 다른 모델 카운터 리셋
        for other_model in list(self.switch_requests.keys()):
            if other_model != model_name:
                self.switch_requests[other_model] = 0

        # 요청 모델 카운터 증가
        self.switch_requests[model_name] += 1

        # 연속 요청 확인
        if self.switch_requests[model_name] >= self.confirmation_count:
            # 확인 완료! 전환 진행
            if model_name == self.last_direction_model:
                # 동일 방향 모델 - 쿨다운 타이머 갱신
                self.switch_time = current_time
                return True

            # 새 모델로 전환
            if model_name != self.current_model_name:
                self.current_model_name = model_name
                self.switch_time = current_time

                # 방향 기반 모델 추적
                if model_name in ["laneD2"]:
                    self.last_direction_model = model_name
                elif model_name == "laneD1":
                    self.last_direction_model = None

                logger.info(f"자동 전환: {model_name}")
                return True
            else:
                # 동일 모델 - 타이머만 갱신
                self.switch_time = current_time
                return True
        else:
            # 아직 확인 부족
            remaining = self.confirmation_count - self.switch_requests[model_name]
            return False

    def check_switch_timeout(self) -> bool:
        """
        모델 전환 타임아웃 확인 (기본 모델로 복귀)

        Returns:
            타임아웃 발생 및 복귀 여부
        """
        if self.current_model_name in ["laneD2"]:
            if time.time() - self.switch_time >= self.switch_duration:
                # 기본 모델(laneD1)로 복귀
                if "laneD1" in self.models:
                    self.current_model_name = "laneD1"
                    self.last_direction_model = None
                    self.switch_requests = {}
                    logger.info("타임아웃 - laneD1로 복귀")
                    return True
                else:
                    logger.warning(
                        f"타임아웃이지만 laneD1 없음 - "
                        f"{self.current_model_name} 유지"
                    )
        return False

    @property
    def latency(self) -> float:
        """
        최근 20 프레임 평균 레이턴시 반환 (초)

        Returns:
            평균 레이턴시
        """
        if self.total_predictions == 0:
            return 0.00
        elif self.total_predictions < 20:
            valid_entries = self.latency_history[:self.total_predictions]
            avg_seconds = np.mean(valid_entries)
            return round(avg_seconds, 3)
        else:
            avg_seconds = np.mean(self.latency_history)
            return round(avg_seconds, 3)

    @property
    def current_model(self) -> str:
        """
        현재 활성 모델 이름 반환

        Returns:
            모델 이름
        """
        return self.current_model_name

    def set_video_stream(self, video_stream: object) -> None:
        """
        비디오 스트림 참조 업데이트

        Args:
            video_stream: 비디오 스트림 객체
        """
        self.video_stream = video_stream

    def get_available_models(self) -> List[str]:
        """
        사용 가능한 모델 목록 반환

        Returns:
            모델 이름 리스트
        """
        return list(self.models.keys())

    def get_model_info(self) -> Optional[Dict]:
        """
        현재 모델 정보 반환

        Returns:
            모델 정보 딕셔너리 또는 None
        """
        if self.current_model_name in self.model_configs:
            config = self.model_configs[self.current_model_name]
            return {
                'name': self.current_model_name,
                'input_width': config['input_width'],
                'input_height': config['input_height'],
                'total_predictions': self.total_predictions,
                'average_latency_ms': self.latency * 1000,  # 밀리초 변환
                'switch_requests': self.switch_requests,
                'confirmation_count': self.confirmation_count
            }
        return None


# 버전 정보
__version__ = '1.0.0'
__author__ = 'BrainAI Co,.Ltd.'
__description__ = 'BrainAI Autonomous Driving Project - Lane Detection'