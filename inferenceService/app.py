import sys
sys.path.append('../')

import torch
import configparser
from fastapi import FastAPI
from utils import test_transform
from pydantic import BaseModel
from base64 import b64decode
from PIL import Image
from io import BytesIO


class Data(BaseModel):
    instances: list[str]


class Result(BaseModel):
    predictions: list[float]


class Model:

    def __init__(self, path: str, device: str) -> None:
        self.model = torch.load(path, map_location=torch.device(device)).eval().to(device)
        self.device = device

    async def preprocess(self, data: Data) -> torch.Tensor:
        return torch.stack(
            [
                test_transform(Image.open(BytesIO(b64decode(b64data))).convert('RGB'))
                for b64data in data.instances
            ]
        ).to(self.device)

    async def predict(self, data: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            return self.model(data)

    async def postprocess(self, data: torch.Tensor) -> dict[str, list[float]]:
        return {
            'predictions': [
                round(predict, 1)
                for predict in
                (data.flatten() * 10)
                .clip(0, 10)
                .cpu()
                .numpy()
                .tolist()
            ]
        }

    async def result(self, data: Data) -> dict[str, list[float]]:
        preprocess = await self.preprocess(data)
        predict = await self.predict(preprocess)
        postprocess = await self.postprocess(predict)
        return postprocess


config = configparser.ConfigParser()
config.read('.cfg')
print(config.sections())
man_model = Model(config['DEFAULT']['man'], config['DEFAULT']['device'])
woman_model = Model(config['DEFAULT']['woman'], config['DEFAULT']['device'])
app = FastAPI()


@app.post('/man/predict')
async def man_predict(data: Data) -> Result:
    return await man_model.result(data)

@app.post('/woman/predict')
async def woman_predict(data: Data) -> Result:
    return await woman_model.result(data)
