from beep_detect.core.time_conversion import ms_to_chunks
from beep_detect.core.file_input_runner import FileInputRunner
import logging

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
  }
}

fir = FileInputRunner(fingerprints, '../../data/Washing machine finish.wav')

fir.run()