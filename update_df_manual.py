import os
import pandas as pd
import logging
from argparse import ArgumentParser


logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())


def dfLoad(datasetPath: str) -> pd.DataFrame:
    columns = ['fileName', 'gender', 'country', 'rate', 'voices', 'img', 'faces']
    imgPaths = os.listdir(datasetPath)
    data = []
    faces = 1

    for fileName in imgPaths:
        _, gender, country, rate, voices = '.'.join(fileName.split('.')[:-1]).split('_')
        with open(os.path.join(datasetPath, fileName), 'rb') as f:
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
    args, _ = parser.parse_known_args()

    _logger.info('load')
    df = dfLoad(args.ds)
    df = pd.concat([pd.read_parquet(args.dst), df])
    _logger.info('save')
    df.to_parquet(args.dst)