---
title: Microphone Configuration
description: "Configure microphone devices for audio input"
icon: microphone
---

## Overview

This guide explains how to configure specific microphone devices for audio input with `GoogleASRInput` and `GoogleASRRTSPInput` plugins in OM1.

## Finding Your Microphone Device

### Method 1: Using PyAudio (Recommended)

Create a Python script to list all available audio input devices:

```python
import pyaudio

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
num_devices = info.get('deviceCount')

print("Available Input Devices:")
print("-" * 60)

for i in range(num_devices):
    device_info = p.get_device_info_by_host_api_device_index(0, i)
    if device_info.get('maxInputChannels') > 0:
        print(f"Device ID: {i}")
        print(f"  Name: {device_info.get('name')}")
        print(f"  Channels: {device_info.get('maxInputChannels')}")
        print(f"  Default Sample Rate: {device_info.get('defaultSampleRate')}")
        print("-" * 60)

p.terminate()
```

Save this script as `list_microphones.py` and run it:

```bash
python3 list_microphones.py
```

**Example Output:**
```
Available Input Devices:
------------------------------------------------------------
Device ID: 0
  Name: Built-in Microphone
  Channels: 2
  Default Sample Rate: 48000.0
------------------------------------------------------------
Device ID: 3
  Name: USB Microphone Array
  Channels: 6
  Default Sample Rate: 48000.0
------------------------------------------------------------
```

### Method 2: Using Linux Command Line Tools

#### Using `pactl` (PulseAudio)

```bash
# List all audio input sources
pactl list sources short

# Or for more detailed information
pactl list sources
```

#### Using `arecord` (ALSA)

```bash
# List all capture hardware devices
arecord -l
```

**Example Output:**
```
**** List of CAPTURE Hardware Devices ****
card 0: PCH [HDA Intel PCH], device 0: ALC294 Analog [ALC294 Analog]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
card 1: Array [Microphone Array], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```

## Configuration

### Using microphone_device_id

Add the `microphone_device_id` parameter to your agent input configuration:

```json5
{
  agent_inputs: [
    {
      type: "GoogleASRInput",
      config: {
        microphone_device_id: 3,  // Use the Device ID from PyAudio
      },
    },
  ],
}
```

### Using microphone_name

Alternatively, you can specify the microphone by name:

```json5
{
  agent_inputs: [
    {
      type: "GoogleASRInput",
      config: {
        microphone_name: "USB Microphone Array",  // Partial name matching
      },
    },
  ],
}
```

### Complete Example: Unitree G1 with Custom Microphone

```json5
{
  version: "v1.0.2",
  hertz: 10,
  name: "iris",
  unitree_ethernet: "enP2p1s0",
  api_key: "openmind_free",
  
  agent_inputs: [
    {
      type: "GoogleASRRTSPInput",
      config: {
        microphone_device_id: 3,  // Specify your USB microphone
        rate: 48000,
        chunk: 12144,
      },
    },
    {
      type: "UnitreeG1LocationsInput",
    },
    // ... other inputs
  ],
  
  // ... rest of config
}
```

## Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `microphone_device_id` | `int` | No | `None` | PyAudio device index. Use `list_microphones.py` to find. |
| `microphone_name` | `str` | No | `None` | Partial name of the microphone device for matching. |
| `rate` | `int` | No | `48000` | Audio sampling rate in Hz. |
| `chunk` | `int` | No | `12144` | Number of frames per buffer. |

**Note:** If both `microphone_device_id` and `microphone_name` are omitted, the system will use the default microphone.

## Troubleshooting

### Issue: No audio input detected

**Solution:**
1. Verify the microphone is connected and recognized:
   ```bash
   # Check if device appears in system
   arecord -l
   ```

2. Test recording with ALSA:
   ```bash
   # Record 5 seconds of audio to test
   arecord -d 5 -D hw:1,0 test.wav
   aplay test.wav
   ```

3. Check PulseAudio is running:
   ```bash
   systemctl --user status pulseaudio
   ```

### Issue: Wrong microphone being used

**Solution:**
1. Run `list_microphones.py` to get the correct device ID
2. Update `microphone_device_id` in your config
3. Restart the OM1 agent

### Issue: PyAudio errors on Ubuntu/Debian

**Solution:**
Install PyAudio dependencies:
```bash
sudo apt-get update
sudo apt-get install python3-pyaudio portaudio19-dev
```

### Issue: Audio quality is poor

**Solution:**
1. Check if the sample rate matches your microphone's native rate
2. Adjust the `chunk` size (try 4096, 8192, or 16384)
3. Verify USB bandwidth if using USB microphone (try different USB port)

## Platform-Specific Notes

### Unitree G1 (ARM Linux)

The Unitree G1 uses a custom network interface. Make sure to:
1. Use `GoogleASRRTSPInput` (not `GoogleASRInput`)
2. Set the correct `unitree_ethernet` interface (usually `enP2p1s0`)
3. Verify the microphone is accessible via USB

### ReSpeaker Microphone Arrays

For ReSpeaker 6-mic or 4-mic arrays:
```json5
{
  type: "GoogleASRInput",
  config: {
    microphone_name: "ReSpeaker",  // Matches "ReSpeaker 4 Mic Array" or similar
    rate: 16000,  // ReSpeaker's native rate
    chunk: 4096,
  },
}
```

## See Also

- [Input Plugin Guide](input.md) - Creating custom input plugins
- [Configuration Guide](config.md) - General configuration options
- [GoogleASRInput API Reference](../api-reference/inputs/google-asr.md)
