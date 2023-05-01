from beep_detect.core.types import FingerprintInMs, SectionAnyInMs, SectionSineInMs

def ms_to_chunks(time_in_ms: int | float, sample_rate: int, chunk_length: int) -> int:
  return int(1e-3 * time_in_ms * sample_rate / chunk_length)

def chunks_to_s(time_in_chunks: int | float, sample_rate: int, chunk_length: int) -> float:
  return time_in_chunks * chunk_length / sample_rate

def chunks_to_ms(time_in_chunks: int | float, sample_rate: int, chunk_length: int) -> float:
  return 1e3 * chunks_to_s(time_in_chunks, sample_rate, chunk_length)
