"""Smoke-test only a synthetic disposable container, never a user's HA."""
import io
import json
import tarfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

base = 'http://127.0.0.1:10520'

def call(path, body=None, token=True):
    headers = {'x-klar-token': 'ci-synthetic-token'} if token else {}
    if body is not None:
        headers['content-type'] = 'application/json'
        body = body if isinstance(body, bytes) else json.dumps(body).encode()
    req = Request(base + path, data=body, headers=headers)
    try:
        with urlopen(req, timeout=20) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()

for attempt in range(90):
    try:
        status, ui = call('/')
        if status == 200:
            break
    except (URLError, TimeoutError):
        pass
    time.sleep(1)
else:
    raise RuntimeError('container did not start')
assert b'Klar UI nicht gebaut' not in ui and b'<script' in ui
snapshot = {'schema_version': '1', 'entities': [
    {'entity_id': f'light.fixture_{i}', 'name': f'Fixture {i}',
     'original_name': 'fixture ' * 25, 'aliases': ['fixture alias ' * 8]} for i in range(2216)],
    'areas': [{'id': 'kantoor', 'name': 'kantoor'}],
    'devices': [{'id': 'office', 'name': 'office', 'area_id': 'kantoor'}],
    'floors': [{'floor_id': 'ground', 'name': 'Ground'}],
    'labels': [{'label_id': 'lighting', 'name': 'Lighting'}], 'assist': None}
snapshot['entities'][0].update(name='kantoor plafond', device_id='office')
snapshot['entities'][1] = {'entity_id': 'binary_sensor.kantoor_raam', 'name': 'kantoor raam', 'area_id': 'kantoor'}
body = json.dumps(snapshot).encode()
assert len(body) > 538682
assert call('/api/v2/home', body, token=False)[0] == 401
status, ack = call('/api/v2/home', body)
assert status == 200, (status, ack)
assert json.loads(ack)['entities'] == 2216
for text in ['Doe het licht in het kantoor uit', 'Kun je het licht in het kantoor even uitdoen?']:
    status, result = call('/api/v2/parse', {'text': text, 'language': 'nl'})
    result = json.loads(result)
    assert status == 200 and result['decision']['type'] == 'execute', result
    assert result['plan']['steps'][0]['intent']['name'] == 'HassTurnOff', result
status, result = call('/api/v2/parse', {'text': 'Welke ramen staan er open?', 'language': 'nl'})
result = json.loads(result)
intent = result['plan']['steps'][0]['intent']
assert intent['name'] == 'HassGetState', result
slots = {slot['name']: slot['value'] for slot in intent['slots']}
assert slots['domain'] == 'binary_sensor' and slots['device_class'] == 'window'
assert slots['response'] == 'list' and slots['state'] == 'on', slots
for text in ['Doe het licht in het kantoor niet uit', 'Kun je het licht in het kantoor niet uitdoen?']:
    status, result = call('/api/v2/parse', {'text': text, 'language': 'nl'})
    result = json.loads(result)
    assert result['decision']['type'] != 'execute', result
assert call('/api/v2/home', b'{}' + b' ' * (8 * 1024 * 1024))[0] == 413
assert call('/api/v2/parse', b'{}' + b' ' * (16 * 1024))[0] == 413
status, archive = call('/api/v2/settings/backup')
assert status == 200
with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
    manifest = json.load(tar.extractfile('manifest.json'))
assert manifest['engine'] == '2026.10.3-rc.2892901', manifest
print('PASS: packaged UI, 2216-entity sync, Dutch commands/window filters/negation, auth, byte limits, engine version')
