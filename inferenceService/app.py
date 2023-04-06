import sys
sys.path.append('../')

import torch
import configparser
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from utils import test_transform
from pydantic import BaseModel
from base64 import b64decode
from PIL import Image
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware


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
man_model = Model(config['DEFAULT']['man'], config['DEFAULT']['device'])
woman_model = Model(config['DEFAULT']['woman'], config['DEFAULT']['device'])
openapi_prefix = config['FASTAPI'].get('openapi_prefix', '')
app = FastAPI(openapi_prefix=openapi_prefix)


app.add_middleware(
    CORSMiddleware,
    allow_origins=config['CORS']['origins'].split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	logging.error(f"error: {exc_str}")
	content = {'status_code': 10422, 'message': exc_str, 'data': None}
	return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

@app.post('/man/predict')
async def man_predict(data: Data) -> Result:
    return await man_model.result(data)

@app.post('/woman/predict')
async def woman_predict(data: Data) -> Result:
    return await woman_model.result(data)
