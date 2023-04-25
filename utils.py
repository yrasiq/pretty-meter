import torch
import torchvision.transforms as transforms
import torchvision.transforms.functional as F
import numpy as np
from PIL import Image
import pandas as pd
from io import BytesIO
from statistics import mean
from torchvision.models.detection import RetinaNet_ResNet50_FPN_V2_Weights


class Dataset(torch.utils.data.Dataset):

    def __init__(self, df: pd.DataFrame, transforms: transforms.Compose = None):
        self.transforms = transforms
        self.df = df
        self.df['voices_weight'] = self.df['voices'] ** 0.5
        self.voices_weight = 1 / (
            self.df['voices_weight'].sort_values().median()
            / self.df['weight'].sort_values().median()
        )

    def __getitem__(self, idx):
        img = Image.open(BytesIO(self.df['img'][idx])).convert('RGB')
        rate = self.df['rate'][idx]
        rate = torch.Tensor([rate])
        weight = self.df['weight'][idx] + (self.df['voices_weight'][idx] - 1) * self.voices_weight
        weight = torch.Tensor([weight])

        if self.transforms is not None:
            img = self.transforms(img)
        return img, rate, weight

    def __len__(self):
        return len(self.df)


class SquarePad:
	def __call__(self, image):
		w, h = image.size
		max_wh = np.max([w, h])
		hp = int((max_wh - w) / 2)
		vp = int((max_wh - h) / 2)
		padding = (hp, vp, hp, vp)
		return F.pad(image, padding, 0, 'constant')


class TrainResult:

    def __init__(self, losses: list[float], diffs: list[float]) -> None:
        self.losses = losses
        self.diffs = diffs

    @classmethod
    def concat(cls, values: list):
        return cls(
            [item for sublist in values for item in sublist.losses],
            [item for sublist in values for item in sublist.diffs]
        )


class TestResult:

    def __init__(self, accuracy: float, loss: float, diff: float,
                min_rate: float, max_rate: float, max_diff: float, df: pd.DataFrame) -> None:
        self.accuracy = accuracy
        self.loss = loss
        self.diff = diff
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.max_diff = max_diff
        self.df = df
    
    @classmethod
    def concat(cls, values: list):
        df = pd.concat([i.df for i in values], ignore_index=True)
        df['rate'] = pd.cut(df['rate'], bins=np.arange(0.0, 1.001, 0.05)).apply(lambda x: x.right)
        df = df.groupby('range', as_index=False).mean()
        return cls(
            mean([i.accuracy for i in values]),
            mean([i.loss for i in values]),
            mean([i.diff for i in values]),
            min([i.min_rate for i in values]),
            max([i.max_rate for i in values]),
            max([i.max_diff for i in values]),
            df
        )


class NotFoundPerson(Exception):
    pass


def weighted_mse_loss(inputs: torch.Tensor, targets: torch.Tensor, weights: torch.Tensor=None):
    loss = (inputs - targets) ** 2
    if weights is not None:
        loss *= weights.expand_as(loss)
    loss = torch.mean(loss)
    return loss

def weighted_l1_loss(inputs: torch.Tensor, targets: torch.Tensor, weights: torch.Tensor=None):
    loss = (inputs - targets).absolute()
    if weights is not None:
        loss *= weights.expand_as(loss)
    loss = torch.mean(loss)
    return loss

def weighted_rmse_loss(inputs: torch.Tensor, targets: torch.Tensor, weights: torch.Tensor=None):
    return weighted_mse_loss(inputs, targets, weights) ** 0.5

def get_person_rect(person_data: dict[str: torch.Tensor], person_index: int, treshold: float=0.66) -> np.ndarray:
    boxes = person_data['boxes'].detach().cpu()[[(person_data['labels'] == person_index) & (person_data['scores'] >= treshold)]].numpy()
    if not boxes.any():
        raise NotFoundPerson
    distances = [np.linalg.norm(box[:2]-box[2:]) for box in boxes]
    return boxes[distances.index(max(distances))]

test_transform = transforms.Compose([
	SquarePad(),
	transforms.Resize((256, 256)),
	transforms.ToTensor()
])

train_transform = transforms.Compose([
	SquarePad(),
    transforms.Resize((256, 256)),
    transforms.RandomCrop((256, 256), padding=32),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.125, contrast=0.125, saturation=(0, 2)),
    transforms.ToTensor(),
])
