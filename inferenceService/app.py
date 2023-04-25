import sys
sys.path.append('../')

import torch
import configparser
import logging
import torchvision.transforms as transforms
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from utils import test_transform, SquarePad, NotFoundPerson, get_person_rect
from pydantic import BaseModel
from base64 import b64decode
from PIL import Image
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
from torchvision.models.detection import retinanet_resnet50_fpn_v2, RetinaNet_ResNet50_FPN_V2_Weights


class Data(BaseModel):
    instances: list[str]


class Result(BaseModel):
    predictions: list[float | None]


class PersonDetector:

    def __init__(self, device: str) -> None:
        self.model = (
            retinanet_resnet50_fpn_v2(weights=RetinaNet_ResNet50_FPN_V2_Weights.COCO_V1)
            .to(device)
            .eval()
        )
        self.person_index = (
            RetinaNet_ResNet50_FPN_V2_Weights
            .COCO_V1
            .meta["categories"]
            .count('person')
        )
        self.img_transform = transforms.Compose([
            SquarePad(),
            transforms.Resize((256, 256)),
        ])
        self.model_transform = RetinaNet_ResNet50_FPN_V2_Weights.COCO_V1.transforms()
        self.device = device

    async def preprocess(self, data: Data) -> tuple[torch.Tensor, list[Image.Image]]:
        images = []
        model_inputs = []
        for b64data in data.instances:
            img = self.img_transform(Image.open(BytesIO(b64decode(b64data))).convert('RGB'))
            model_input = self.model_transform(img)
            images.append(img)
            model_inputs.append(model_input)
        model_inputs = torch.stack(model_inputs).to(self.device)
        return model_inputs, images

    async def predict(
        self,
        data: torch.Tensor,
        images: list[Image.Image]
    ) -> tuple[
            list[dict[str, torch.Tensor]],
            list[Image.Image]
        ]:
        with torch.no_grad():
            return self.model(data), images

    async def postprocess(self, boxes: list[dict[str, torch.Tensor]], images: list[Image.Image | None]) -> list[Image.Image]:
        for i, box in enumerate(boxes):
            box['boxes'] = box['boxes'].detach().cpu().to(torch.int64)
            box['scores'] = box['scores'].detach().cpu()
            box['labels'] = box['labels'].detach().cpu()
            try:
                images[i] = images[i].crop(get_person_rect(box, self.person_index))
            except NotFoundPerson:
                images[i] = None
        return images

    async def result(self, data: Data) -> list[Image.Image]:
        model_inputs, images = await self.preprocess(data)
        predict, images = await self.predict(model_inputs, images)
        postprocess = await self.postprocess(predict, images)
        return postprocess


class Model:

    def __init__(self, path: str, device: str) -> None:
        self.model = (
            torch.load(path, map_location=torch.device(device))
            .to(device)
            .eval()
        )
        self.device = device

    async def preprocess(
            self,
            images: list[Image.Image | None]
        ) -> tuple[torch.Tensor | None, list[int]]:
        not_found_person_indexes = []
        tensors = []
        for i, image in enumerate(images):
            if image is None:
                not_found_person_indexes.append(i)
            else:
                tensors.append(test_transform(image))
        if tensors:
            tensors = torch.stack(tensors).to(self.device)
        else:
            tensors = None
        return tensors, not_found_person_indexes

    async def predict(
            self,
            data: torch.Tensor,
            not_found_person_indexes: list[int]
        ) -> tuple[torch.Tensor, list[int]]:
        with torch.no_grad():
            return self.model(data), not_found_person_indexes

    async def postprocess(
            self,
            data: torch.Tensor,
            not_found_person_indexes: list[int]
        ) -> dict[str, list[float]]:
        predictions = [None] * (len(data) + len(not_found_person_indexes))
        data = (data.flatten() * 10).clip(0, 10).cpu().numpy().tolist()
        gen = (i for i in data)

        for i, _ in enumerate(predictions):
            if i not in not_found_person_indexes:
                predictions[i] = round(next(gen), 1)

        return {'predictions': predictions}

    async def result(self, data: list[Image.Image | None]) -> dict[str, list[float | None]]:
        tensors, not_found_person_indexes = await self.preprocess(data)
        if tensors is None:
            return {'predictions': [None] * len(data)}
        predict, not_found_person_indexes = await self.predict(tensors, not_found_person_indexes)
        postprocess = await self.postprocess(predict, not_found_person_indexes)
        return postprocess


config = configparser.ConfigParser()
config.read('.cfg')
man_model = Model(config['DEFAULT']['man'], config['DEFAULT']['device'])
woman_model = Model(config['DEFAULT']['woman'], config['DEFAULT']['device'])
person_detector = PersonDetector(config['DEFAULT']['device'])
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
    return await man_model.result(
        await person_detector.result(data)
    )

@app.post('/woman/predict')
async def woman_predict(data: Data) -> Result:
    return await woman_model.result(
        await person_detector.result(data)
    )
