import os
import logging
import pandas as pd
from base64 import b64encode


logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())


datasetPath = 'dataset'
columns = ['fileName', 'gender', 'country', 'rate', 'voices', 'b64img']

def load(columns: list[str], datasetPath: str) -> pd.DataFrame:
    imgPaths = os.listdir(datasetPath)
    data = []

    for fileName in imgPaths:
        _, gender, country, rate, voices = '.'.join(fileName.split('.')[:-1]).split('_')
        with open(os.path.join(datasetPath, fileName), 'rb') as f:
            b64img = b64encode(f.read()).decode()
        data.append((fileName, gender, country, rate, voices, b64img))

    return pd.DataFrame(data, columns=columns)

def removeDuplicates(df: pd.DataFrame, datasetPath: str) -> int:
    dfGrouped = df.groupby(['gender', 'country', 'rate', 'voices', 'b64img'])
    delete = []

    for groupName in dfGrouped.groups:
        group = dfGrouped.get_group(groupName)
        if len(group) > 1:
            delete += list(group['fileName'])[1:]

    for fileName in delete:
        os.remove(os.path.join(datasetPath, fileName))

    return len(delete)

def main() -> None:
    _logger.info('load data')
    df = load(columns, datasetPath)
    _logger.info('remove duplicates')
    removed = removeDuplicates(df, datasetPath)
    _logger.info(f'removed {removed} duplicates')

if __name__ == '__main__':
    main()