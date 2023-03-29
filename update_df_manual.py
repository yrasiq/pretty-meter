import os
import pandas as pd
import logging
from argparse import ArgumentParser
from PIL import Image
import torchvision.transforms as transforms
import numpy as np
import torchvision.transforms.functional as F
from io import BytesIO
from utils import SquarePad
from tqdm import tqdm


logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())


transform = transforms.Compose([
	SquarePad(),
	transforms.Resize((256, 256)),
])

def dfLoad(datasetPath: str, transforming: bool = False) -> pd.DataFrame:
    columns = ['fileName', 'gender', 'country', 'rate', 'voices', 'img', 'faces']
    imgPaths = os.listdir(datasetPath)
    data = []
    faces = 1

    for fileName in tqdm(imgPaths):
        _, gender, country, rate, voices = '.'.join(fileName.split('.')[:-1]).split('_')
        with open(os.path.join(datasetPath, fileName), 'rb') as f:
            if transforming:
                io = BytesIO()
                img = Image.open(f)
                img = transform(img)
                img.save(io, format='png')
                img = io.getvalue()
            else:
                img = f.read()

        data.append((fileName, gender, country, rate, voices, img, faces))

    df = pd.DataFrame(data, columns=columns)
    df['rate'] = df['rate'].astype(float)
    df['voices'] = df['voices'].astype(float)
    return df

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--ds', required=True)
    parser.add_argument('--dst', required=True)
    parser.add_argument('--transforming', action='store_true', default=False)
    args, _ = parser.parse_known_args()

    _logger.info('load')
    df = dfLoad(args.ds, args.transforming)
    df = pd.concat([pd.read_parquet(args.dst), df])
    _logger.info('save')
    df.to_parquet(args.dst)