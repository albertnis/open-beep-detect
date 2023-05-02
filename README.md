# Open Beep Detect

An open-source beep detection system. Perfect for listening to appliances.

It's early days for Open Beep Detect but here's an overview of what it is and what it might be one day:

**Features**:

- Simple and explainable (no machine learning here)
- Detect multiple devices
- Run from either microphone or audio file

**Future goals**:

- MQTT publish upon complete match
- Web server for configuration and monitoring
- Mode to learn new fingerprints
- Port to ESP32 or similar microcontroller

## How it works

The `ChunkProcessor` class is initialised with multiple fingerprints to match. Each fingerprint defines a beep in terms of frequencies, lengths and repetitions. After initialisation, the chunk processor is run with successive chunks of audio. Each audio chunk is analysed for frequency peaks which are then matched against the fingerprints. The processor tracks the state of previous matches-in-progress and returns any matches which are complete.

The chunk processor does not care where the audio chunks come from; fetching audio is the responsibility of the caller. Two such callers are implemented here for example: the `FileInputRunner` which takes chunks from a .wav file and the `DeviceInputRunner` which uses PyAudio to fetch chunks from an input device such as a microphone.

Usage examples for fingerprints and runners can be found in [beep_detect/core/main.py](./beep_detect/core/main.py).

## Setup

Install dependencies

```shell
poetry install
```

Optionally, install dependencies for analysis in Jupyter notebook

```shell
poetry install --with notebooks
```

## Run locally

Run main file

```shell
cd beep_detect/core
python main.py
```

Or start web server (this currently doesn't do much and is a work in progress)

```shell
python -m beep_detect.web
```
