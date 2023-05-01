from beep_detect.core.types import FingerprintInMs, ChunkMap
from beep_detect.core.time_conversion import ms_to_chunks

def fingerprint_to_chunkmap(fingerprint: FingerprintInMs, sample_rate: int, chunk_length: int) -> ChunkMap:
  mtc = lambda m: ms_to_chunks(m, sample_rate, chunk_length)
  pattern = fingerprint['pattern']
  frequencies_to_match_by_chunk = []
  aggregate_start_chunk = mtc(min([section['start_ms'] for section in pattern]))
  aggregate_end_chunk = mtc(max([section['end_ms'] for section in pattern]))

  for i_chunk in range(aggregate_start_chunk, aggregate_end_chunk):
    relevant_sections = [p for p in pattern if mtc(p['start_ms']) <= i_chunk and mtc(p['end_ms']) > i_chunk]
    for section in relevant_sections:
      chunk_freqs = []
      if section['type'] == 'sine':
        chunk_freqs.append(section['frequency'])
      elif section['type'] == 'any':
        pass
      else:
        section_type = section['type']
        raise ValueError(f'Section has unrecognised type "{section_type}"')
      
      frequencies_to_match_by_chunk.append(chunk_freqs)
    
  result: ChunkMap = {
    'max_period_chunks': mtc(fingerprint['max_period_ms']),
    'repetitions': fingerprint['repetitions'],
    'frequencies_to_match_by_chunk': frequencies_to_match_by_chunk
    }
  
  return result