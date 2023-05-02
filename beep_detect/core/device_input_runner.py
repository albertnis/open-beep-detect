import pyaudio
import logging as log
from math import log2
import numpy as np
import array
from typing import Callable

from beep_detect.core.chunk_processor import ChunkProcessor
from beep_detect.core.types import FingerprintInMs

class DeviceInputRunner():
    def __init__(
            self,
            fingerprints: dict[str, FingerprintInMs],
            match_callback: Callable[[str], None],
            target_chunk_duration_ms: float = 30
        ) -> None:
        self.pa = pyaudio.PyAudio()

        # Obtain device from default
        device = self.pa.get_default_input_device_info()
        if device is None:
            raise IOError('No default input device was found')

        self.device_index = int(device['index'])
        self.device_framerate = int(device['defaultSampleRate'])

        log.info(f'Using device "{device["name"]}", index {self.device_index}, sample rate {self.device_framerate}Hz')

        # Select sample size
        samples_per_minimum_chunk = self.device_framerate * target_chunk_duration_ms * 1e-3
        self.samples_per_chunk = 2 ** round(log2(samples_per_minimum_chunk))
        chunk_duration_ms = 1e3 * self.samples_per_chunk / self.device_framerate

        log.info(f'Minimum {samples_per_minimum_chunk} samples per {target_chunk_duration_ms}ms chunk rounded to nearest power of 2: {self.samples_per_chunk} per {chunk_duration_ms:.2f}ms')

        # Set up chunk processor

        self.chunk_processor = ChunkProcessor(
            fingerprints,
            self.device_framerate,
            self.samples_per_chunk
        )

        self.match_callback = match_callback
        self.stream = None

    def __enter__(self):
        log.debug('Starting device stream')
        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            input_device_index=self.device_index,
            channels=1,
            rate=self.device_framerate,
            input=True,
            frames_per_buffer=self.samples_per_chunk,
            stream_callback=self.handle_input_buffer
        )

        self.stream.start_stream()
        return self

    def handle_input_buffer(self, in_data: bytes | None, frame_count, time_info, status):
        log.debug('Handling input buffer')
        if in_data is None:
            raise IOError('Input stream contained no data')

        datapoints = array.array('H', in_data)
        
        matched_ids = self.chunk_processor.analyse_chunk_for_match(datapoints)

        for id in matched_ids:
            self.match_callback(id)

        return (in_data, pyaudio.paContinue)

    def __del__(self):
        self._destroy()

    def __exit__(self, *args):
        self._destroy()

    def _destroy(self):
        log.debug('Ending device stream')
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()

        self.pa.terminate()