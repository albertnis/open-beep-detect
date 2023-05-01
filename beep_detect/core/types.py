from typing import TypedDict, Literal, Union

class FingerprintInMs(TypedDict):
    repetitions: int
    max_period_ms: int
    pattern: list['SectionInMs']

class SectionSineInMs(TypedDict):
    type: Literal['sine']
    frequency: int
    start_ms: int
    end_ms: int

class SectionAnyInMs(TypedDict):
    type: Literal['any']
    start_ms: int
    end_ms: int

SectionInMs = Union[SectionAnyInMs, SectionSineInMs]

class ChunkMap(TypedDict):
    repetitions: int
    max_period_chunks: int
    frequencies_to_match_by_chunk: list[list[float]]