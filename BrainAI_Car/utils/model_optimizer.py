"""
Model Optimizer Module

TensorFlow 모델을 OpenVINO IR 형식으로 변환하는 모듈입니다.
"""

import os
import logging
import shutil 
from pathlib import Path
from typing import Optional, Tuple

import tensorflow as tf
import openvino as ov


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelOptimizer:
    """TensorFlow 모델을 OpenVINO IR 형식으로 변환하는 클래스"""

    def __init__(self, input_shape: Tuple[int, int, int, int] = (1, 224, 224, 3)):
        """
        Args:
            input_shape: 모델 입력 shape (batch, height, width, channels)
        """
        self.input_shape = input_shape
        logger.info(f"ModelOptimizer 초기화 완료 - Input shape: {input_shape}")

    def load_keras_model(self, model_path: str) -> tf.keras.Model:
        """
        Keras 모델 로드

        Args:
            model_path: Keras 모델 파일 경로

        Returns:
            로드된 TensorFlow Keras 모델

        Raises:
            FileNotFoundError: 모델 파일이 존재하지 않을 때
            ValueError: 모델 로드 중 오류 발생 시
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_path}")

        try:
            logger.info(f"Keras 모델 로드 중: {model_path}")
            
            # **[핵심 수정 사항]:** compile=False를 사용하여 Loss, Optimizer 등 
            # 직렬화 문제를 일으킬 수 있는 컴파일 관련 객체의 로드를 건너뜁니다.
            model = tf.keras.models.load_model(model_path, compile=False) 
            
            logger.info("Keras 모델 로드 완료")
            return model
        except Exception as e:
            # Custom Objects 문제가 있다면 이 부분에 추가 정의 필요
            # 예: custom_objects={"CustomLayer": CustomLayerClass}
            raise ValueError(f"모델 로드 실패: {str(e)}")

    def convert_to_openvino(
        self,
        model: tf.keras.Model,
        example_input: Optional[tf.Tensor] = None
    ) -> ov.Model:
        """
        TensorFlow 모델을 OpenVINO IR 형식으로 변환 (SavedModel 경로 사용)

        Args:
            model: TensorFlow Keras 모델
            example_input: 예제 입력 텐서 (None일 경우 기본값 사용)

        Returns:
            변환된 OpenVINO 모델
        """
        
        # 1. 임시 SavedModel 경로 설정 및 생성
        temp_dir = Path("./temp_ov_convert")
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except OSError as e:
                 logger.warning(f"임시 디렉토리 삭제 실패: {e}. 수동으로 제거 필요.")
        temp_dir.mkdir(exist_ok=True)
        
        # 2. Keras 모델을 OpenVINO 변환에 권장되는 SavedModel 형식으로 저장
        try:
            logger.info(f"모델을 임시 SavedModel 형식으로 저장 중: {temp_dir}")
            # compile=False로 로드했더라도 tf.saved_model.save는 모델 구조 저장을 시도합니다.
            tf.saved_model.save(model, str(temp_dir)) 
            logger.info("SavedModel 저장 완료")
        except Exception as e:
            logger.error(f"SavedModel 저장 실패: {str(e)}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise # 저장 실패 시 변환 진행 불가
        
        # 3. SavedModel 경로를 사용하여 OpenVINO로 변환
        if example_input is None:
            example_input = tf.zeros(self.input_shape, dtype=tf.float32)

        try:
            logger.info("OpenVINO 형식으로 변환 중 (SavedModel 경로 사용)...")
            ov_model = ov.convert_model(
                str(temp_dir),             
                example_input=example_input
            )
            logger.info("OpenVINO 변환 완료")
        except Exception as e:
            logger.error(f"OpenVINO 변환 실패: {str(e)}")
            raise
        finally:
            # 4. 임시 SavedModel 파일 정리 (성공/실패와 관계없이 정리 시도)
            try:
                shutil.rmtree(temp_dir)
                logger.info("임시 SavedModel 디렉토리 정리 완료")
            except OSError as e:
                logger.warning(f"임시 디렉토리 최종 정리 실패: {e}")

        return ov_model

    def save_openvino_model(self, ov_model: ov.Model, output_path: str) -> None:
        """
        OpenVINO 모델을 파일로 저장

        Args:
            ov_model: OpenVINO 모델
            output_path: 출력 파일 경로 (.xml)

        Raises:
            OSError: 파일 저장 중 오류 발생 시
        """
        try:
            # 출력 디렉토리 생성
            output_dir = Path(output_path).parent
            if output_dir != Path('.'):
                output_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"OpenVINO 모델 저장 중: {output_path}")
            ov.save_model(ov_model, output_path)
            logger.info("OpenVINO 모델 저장 완료")

            # .bin 파일도 생성되었는지 확인
            bin_path = Path(output_path).with_suffix('.bin')
            if bin_path.exists():
                logger.info(f"관련 파일 생성됨: {bin_path}")
            else:
                logger.warning(f"관련 .bin 파일이 생성되지 않았거나 경로가 다릅니다.")
        except Exception as e:
            raise OSError(f"모델 저장 실패: {str(e)}")

    def optimize_model(
        self,
        keras_model_path: str,
        output_path: str,
        example_input: Optional[tf.Tensor] = None
    ) -> None:
        """
        전체 최적화 프로세스 실행

        Args:
            keras_model_path: Keras 모델 파일 경로
            output_path: OpenVINO 모델 출력 경로
            example_input: 예제 입력 텐서
        """
        logger.info("=" * 60)
        logger.info("모델 최적화 프로세스 시작")
        logger.info("=" * 60)

        # 1. Keras 모델 로드
        model = self.load_keras_model(keras_model_path)

        # 2. OpenVINO로 변환
        ov_model = self.convert_to_openvino(model, example_input)

        # 3. 저장
        self.save_openvino_model(ov_model, output_path)

        logger.info("=" * 60)
        logger.info("모델 최적화 프로세스 완료")
        logger.info("=" * 60)


def main():
    """메인 실행 함수"""
    # 모델 경로 설정
    keras_model_path = "models_laneD1/brainai_car_laneD1_mobilenet_final.keras"
    output_model_path = "models/laneD1/laneD1.xml"

    # ModelOptimizer 인스턴스 생성
    optimizer = ModelOptimizer(input_shape=(1, 224, 224, 3))

    # 명시적인 예제 입력 텐서 (shape 지정을 위해)
    input_shape = optimizer.input_shape
    example_input = tf.zeros(input_shape, dtype=tf.float32)

    try:
        # 모델 최적화 실행
        logger.info(f"입력 모델: {keras_model_path}")
        logger.info(f"출력 모델: {output_model_path}")
        
        optimizer.optimize_model(
            keras_model_path,
            output_model_path,
            example_input=example_input
        )
        
        logger.info("✓ 모델 최적화 성공!")
        
    except FileNotFoundError as e:
        logger.error(f"파일을 찾을 수 없습니다: {str(e)}")
        logger.error("경로를 확인해주세요.")
        
    except Exception as e:
        logger.error(f"최적화 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()


# 버전 정보
__version__ = '1.0.0'
__author__ = 'BrainAI Co,.Ltd.'
__description__ = 'BrainAI Autonomous Driving Project - Model Optimizer (Handling Serialization Errors)'