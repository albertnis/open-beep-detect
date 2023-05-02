from beep_detect.core.time_conversion import ms_to_chunks
from beep_detect.core.file_input_runner import FileInputRunner
import logging
from beep_detect.core.device_input_runner import DeviceInputRunner
import time
from datetime import datetime

from beep_detect.core.types import FingerprintInMs

logging.getLogger().setLevel(logging.DEBUG)

fingerprints: dict[str, FingerprintInMs] = {
  "washing": {
    'repetitions': 5,
    'max_period_ms': 1400,
    'pattern':
      [
        {
          'type': 'sine',
          'frequency': 3300,
          'start_ms': 0,
          'end_ms': 400
        },
        {
          'type': 'any',
          'start_ms': 401,
          'end_ms': 800
        }
      ]
  },
  "microwave": {
    'repetitions': 5,
    'max_period_ms': 1000,
    'pattern':
      [
        {
          'type': 'sine',
          'frequency': 2030,
          'start_ms': 0,
          'end_ms': 150
        },
        {
          'type': 'any',
          'start_ms': 151,
          'end_ms': 400
        }
      ]
  },
}

# fir = FileInputRunner(fingerprints, '../../data/Washing machine finish.wav')
# fir.run()

def match_callback(fingerprint_id):
    logging.info(f'{datetime.now()}: Match found for {fingerprint_id}')

with DeviceInputRunner(fingerprints, match_callback) as d:
    while d.stream is not None and d.stream.is_active():
        time.sleep(0.5)
