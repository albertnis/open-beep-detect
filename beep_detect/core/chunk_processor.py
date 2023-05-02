import array
import numpy as np
from scipy.fft import rfftfreq, rfft
from scipy.signal import find_peaks
import logging as log
from timeit import default_timer as timer
from threading import Lock
from math import log2
from beep_detect.core.fingerprint_to_chunkmap import fingerprint_to_chunkmap
from beep_detect.core.time_conversion import ms_to_chunks
from beep_detect.core.types import ChunkMap, FingerprintInMs

class ChunkProcessor:
    '''
    Class responsible for analysing each individual chunk of audio and determining whether a match has been made to a predefined chunk. A chunk consists of multiple samples of audio.
    '''

    def __init__(
          self,
          fingerprints: dict[str, FingerprintInMs],
          sample_rate: int,
          chunk_length: int,
          peak_prominence: float = 8,
          peak_distance: float = 8,
          tolerance_f: float = 0.03,
          tolerance_t_ms: float = 50
        ) -> None:
        '''
        Initialise a `ChunkProcessor`

        ## Args:

        - fingerprints (dict): Mapping of fingerprint name to the fingerprint definition with time expressed as number of chunks.
        - frequency_bands (list[int]): Sample frequencies for mapping from rFFT output to frequencies. Usually the output of `scipy.rfftfreq(chunk_length, d=1/sample_rate)`.
        - peak_prominence (int, default 12): Prominence to use for decting frequency peaks. Used as the `prominence` argument when calling numpy's `find_peaks` method. Increasing this will decrease sensitivity.
        - peak_distance (int, default 12): Distance to use for decting frequency peaks. Used as the `distance` argument when calling numpy's `find_peaks` method. Increasing this will decrease sensitivity.
        - tolerance_f (int, default 0.03): Frequencies detected within this relative tolerance will match frequencies specified in the chunkmap. Increasing this will decrease sensitivity.
        - tolerance_t_ms (int, default 60): Maximum number of consecutive non-matching ms that will be ignored while matching a fingerprint. Increasing this will decrease sensitivity.
        '''

        # Set
        self.fingerprints = fingerprints
        self.sample_rate = sample_rate
        self.chunk_length = chunk_length
        self.peak_prominence = peak_prominence
        self.peak_distance = peak_distance
        self.tolerance_f = tolerance_f

        # Validate
        self._warn_if_chunk_length_not_power_of_2()

        # Derive
        self.tolerance_t = ms_to_chunks(tolerance_t_ms, self.sample_rate, self.chunk_length)
        self.frequency_bands = rfftfreq(self.chunk_length, d=1/self.sample_rate)
        self.chunkmaps = { k: fingerprint_to_chunkmap(f, self.sample_rate, self.chunk_length) for k, f in fingerprints.items() }
        log.info(f'Chunk processor initialised with chunkmaps {self.chunkmaps}')

        # Initialise
        self.analysis_lock = Lock()
        self.match_state = { # For each chunkmap, initialise the the current state of matching
           k: {
              'repetition': 0,
              'chunk': 0,
              'chunks_since_last_repetition': 0,
              'accumulated_errors': 0
           } for k in self.fingerprints.keys()
        }

    def analyse_chunk_for_match(self, chunk, with_lock=True) -> set[str]:
        '''
        Analyse a chunk of audio to determine whether that chunk completes a match for any of the fingerprints provided in the chunkmap

        This is achieved by evaluating the peak frequencies in the chunk then incorporating previous state for each fingerprint to see whether the chunk progresses a match, resets a match, or completes a match

        ## Args:

        - chunk (list): List or np.array of samples within the chunk. For best FFT performance, consider making the length a power of 2.
        - with_lock (bool, default True): Use a lock to prevent this method from being called concurrently

        ## Returns:

        - (set[str]): fingerprint IDs which had a match completed by this chunk
        '''
        if with_lock:
            with self.analysis_lock:
                return self._analyse_chunk_for_match(chunk)

        return self._analyse_chunk_for_match(chunk)
    
    def _analyse_chunk_for_match(self, chunk: list[int]) -> set[str]:
        start_time = timer()

        # Ensure chunk length is as expected
        chunk_length = len(chunk)
        if chunk_length != self.chunk_length:
           log.warning(f'Chunk length has changed from {self.chunk_length} to {chunk_length}. Frequency bands will be recalculated.')
           self.chunk_length = chunk_length
           self.frequency_bands = rfftfreq(self.chunk_length, d=1/self.sample_rate)
           self._warn_if_chunk_length_not_power_of_2()
        
        # Compute real FFT and normalise to decibels (dB)
        freq_vals = np.absolute(rfft(chunk)[1:]) # type: ignore
        freq_db = 10*np.log10(freq_vals) # type: ignore

        # Compute frequency peaks and normalise to Hertz (Hz)
        freq_peaks_i = find_peaks(freq_db, prominence=self.peak_prominence, distance=self.peak_distance)[0]
        freq_peaks = [self.frequency_bands[peak] for peak in freq_peaks_i]

        # Compute matches and update state
        matched_fingerprint_keys = self._analyse_peaks_for_match(freq_peaks)

        end_time = timer()
        processing_duration_ms = (end_time - start_time) * 1e3
        chunk_durations_ms = self.chunk_length / self.sample_rate * 1e3
        log.debug(f'Chunk of duration {chunk_durations_ms:.3f}ms analysed in {processing_duration_ms:.3f}ms')

        return matched_fingerprint_keys

    def _analyse_peaks_for_match(self, freq_peaks: list) -> set[str]:
        
        # Assess each chunkmap to see if match status has changed
        fingerprint_matches = set()
        for k, state in self.match_state.items():
          chunkmap = self.chunkmaps[k]
          
          # Does the chunk match given the previous match state?
          matched = self._matches_chunkmap_freqs_at_index(
            chunkmap['frequencies_to_match_by_chunk'],
            self.tolerance_f,
            state['chunk'],
            freq_peaks
          )

          # If the match failed, did it fall within tolerance for missed chunks?
          missed_within_tolerance = not matched and state['chunk'] > 0 and state['accumulated_errors'] < self.tolerance_t
          if missed_within_tolerance:
            # Record that this miss has been allowed
            state['accumulated_errors']  += 1
          if matched:
            # Reset errors
            log.debug(f'{k}: Peaks {freq_peaks} exact match for chunk {chunkmap["frequencies_to_match_by_chunk"][state["chunk"]]}')
            state['accumulated_errors'] = 0

          # Now assess the outcome:
          if matched or missed_within_tolerance:
            # Chunk is as good as a match
            if state['chunk'] >= len(chunkmap['frequencies_to_match_by_chunk']) - 1:
              # Entire chunkmap has been matched -> Phase match completed! Reset for next repetition
              state['chunk'] = 0
              state['repetition'] += 1
              state['chunks_since_last_repetition'] = 0
              state['accumulated_errors'] = 0
            else:
              # -> Look for next match within the chunkmap
              state['chunk'] += 1
              state['chunks_since_last_repetition'] += 1
          elif state['repetition'] > 0 and state['chunks_since_last_repetition'] <= self.chunkmaps[k]['max_period_chunks']:
            # Chunk is not a match -> reset but keep waiting for next phase
            state['chunk'] = 0
            state['chunks_since_last_repetition'] += 1
            state['accumulated_errors']  = 0
          else:
            # No match and no more phases -> reset state for this fingerprint
            state['chunk'] = 0
            state['accumulated_errors']  = 0
            state['chunks_since_last_repetition'] = 0
            state['repetition'] = 0
          
          # Check for fingerprint match
          if state['repetition'] == self.fingerprints[k]['repetitions']:
            # Fingerpring match completed!
            # -> Add to matches to return
            fingerprint_matches.add(k)

            # -> Reset state for this fingerprint
            state['chunk'] = 0
            state['repetition'] = 0
            state['chunks_since_last_repetition'] = 0
            state['accumulated_errors']  = 0

        log.debug(f'State after this chunk is {self.match_state}')

        return fingerprint_matches

    def _matches_chunkmap_freqs_at_index(self, chunkmap_freqs: list[list[float]], freq_tolerance, index, frequencies):
      expected_freqs = chunkmap_freqs[index]
      
      if len(expected_freqs) == 0:
          return True  

      matched_freqs = 0
      for actual_freq in frequencies:
        for expected_freq in expected_freqs:
          if np.isclose(actual_freq, expected_freq, rtol=freq_tolerance):
            matched_freqs += 1
            if matched_freqs == len(expected_freqs):
              return True
            
      return False
    
    def _warn_if_chunk_length_not_power_of_2(self) -> None:
       if log2(self.chunk_length) % 1 != 0:
          log.warning(f'Log level of {self.chunk_length} is not a power of 2. Use a power of 2 for best performance.')
