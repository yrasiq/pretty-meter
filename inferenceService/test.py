import sys
sys.path.append('../')

import pytest
import json
from httpx import AsyncClient
from httpx import Response
from app import app
from base64 import b64encode


base_url = 'http://test'


async def get_predict(uri: str, img_path: str, instances_size: int, ac: AsyncClient) -> Response:
    with open(img_path, 'rb') as f:
        img = b64encode(f.read()).decode('utf-8')
    data = json.dumps({'instances': [img] * instances_size})
    return await ac.post(uri, data=data)

def assert_predict(resp: Response, instances_size: int) -> None:
    assert resp.status_code == 200
    result = resp.json()
    assert result.get('predictions')
    assert len(result['predictions']) == instances_size
    for predict in result['predictions']:
        assert isinstance(predict, (float, None))
        assert predict is None or predict >= 0.0
        assert predict is None or predict <= 10.0
        assert len(str(predict)) == 3


@pytest.mark.anyio
async def test_predict() -> None:
    instances_size = 2
    async with AsyncClient(app=app, base_url=base_url) as ac:
        resp_m = await get_predict('/man/predict', 'm_test_img', instances_size, ac)
        resp_w = await get_predict('/woman/predict', 'w_test_img', instances_size, ac)
    assert_predict(resp_m, instances_size)
    assert_predict(resp_w, instances_size)
