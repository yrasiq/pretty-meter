import pandas as pd
import logging
import cv2
import numpy as np
from argparse import ArgumentParser
from insightface.app import FaceAnalysis

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--pqt', required=True)
    parser.add_argument('--dst', required=True)
    args, _ = parser.parse_known_args()

    _logger.info('load df')
    df = pd.read_parquet(args.pqt)

    app = FaceAnalysis(
        allowed_modules=['detection'],
        providers=['CPUExecutionProvider', 'CUDAExecutionProvider']
    )
    app.prepare(ctx_id=0, det_size=(640, 640))

    _logger.info('find faces')
    df['faces'] = pd.Series(dtype=pd.Int16Dtype)
    for i, img in enumerate(df['img']):
        img = cv2.imdecode(np.frombuffer(img, np.uint8), cv2.IMREAD_COLOR)
        try:
            faces = app.get(img)
        except AttributeError:
            _logger.info(f'exception on {i} record')
            continue

        maxDistance = 0
        maxDistanceIndex = None
        for ii, face in enumerate(faces):
            face['maxDistance'] = False
            face['distance'] = np.linalg.norm(face['bbox'][:2]-face['bbox'][2:4])
            if face['distance'] > maxDistance:
                maxDistance = face['distance']
                maxDistanceIndex = ii

        if maxDistanceIndex is not None:
            faces[maxDistanceIndex]['maxDistance'] = True

        mainFaces = 0
        for face in faces:
            confidence = face['det_score']
            if (confidence > 0.66) and (face['maxDistance'] or maxDistance / face['distance'] < 2):
                mainFaces += 1

        df['faces'].iat[i] = mainFaces

        if ((i + 1) % 1000 == 0) or i + 1 == len(df):
            _logger.info(f'{i + 1}/{len(df)}')

    _logger.info('save df')
    df.to_parquet(args.dst)
