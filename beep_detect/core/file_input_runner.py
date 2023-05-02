from beep_detect.core.types import FingerprintInMs
from chunk_processor import ChunkProcessor
import wave
import array
import logging as log
from beep_detect.core.time_conversion import chunks_to_s

class FileInputRunner():
    def __init__(self, fingerprints: dict[str, FingerprintInMs], file_name: str) -> None:
        wf = wave.open(file_name, 'rb')
        data = wf.readframes(wf.getnframes())
        self.input_sample_rate = wf.getframerate()
        self.datapoints = array.array('H', data)
        self.chunk_length = 2048

        self.chunk_processor = ChunkProcessor(
            fingerprints,
            self.input_sample_rate,
            self.chunk_length
        )

    def run(self):
        events = []
        for i_chunk in range(10*self.input_sample_rate // self.chunk_length, len(self.datapoints) // self.chunk_length):
          i_sample_start = i_chunk*self.chunk_length
          i_sample_end = i_sample_start + self.chunk_length

          t = chunks_to_s(i_chunk+1, self.input_sample_rate, self.chunk_length)
          
          log.debug(f't={t:2f}s;i={i_chunk}')

          results = self.chunk_processor.analyse_chunk_for_match(self.datapoints[i_sample_start:i_sample_end])

          for match in results:
              events.append({'t': t})
              log.info(f't={t:2f}s;Match for {match}!')

          i_chunk += 1

        log.info(f'{len(events)} events detected: {events}')