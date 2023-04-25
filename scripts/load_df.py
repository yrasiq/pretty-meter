import os
import pandas as pd
import logging
from argparse import ArgumentParser
from tqdm import tqdm


logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())

columns = ['fileName', 'gender', 'country', 'rate', 'voices', 'img']

def dfLoad(datasetPath: str) -> list[pd.DataFrame]:
    imgPaths = os.listdir(datasetPath)
    dfs = []
    data = []
    for fileName in tqdm(imgPaths):
        current_path = os.path.join(datasetPath, fileName)
        if os.path.isdir(current_path):
            dfs += dfLoad(current_path)
        else:
            _, gender, country, rate, voices = '.'.join(fileName.split('.')[:-1]).split('_')
            with open(current_path, 'rb') as f:
                img = f.read()
            data.append((fileName, gender, country, rate, voices, img))
    df = pd.DataFrame(data, columns=columns)
    del data
    df['rate'] = df['rate'].astype(float)
    df['voices'] = df['voices'].astype(float)
    return [df] + dfs

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--ds', required=True)
    parser.add_argument('--dst', required=True)
    args, _ = parser.parse_known_args()

    _logger.info('load')
    df = pd.concat(dfLoad(args.ds), ignore_index=True)
    _logger.info('save')
    df.to_parquet(args.dst)
