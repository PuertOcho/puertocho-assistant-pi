# Porcupine Models Directory

This directory contains the wake word models for Porcupine:

- `porcupine_params_es.pv` - Spanish language model parameters
- `Puerto-ocho_es_raspberry-pi_v3_0_0.ppn` - Custom "Puerto-ocho" wake word model

## Getting the Models

1. **Spanish Parameters Model**:
   - Download from: https://github.com/Picovoice/porcupine/tree/master/lib/common
   - File: `porcupine_params_es.pv`

2. **Custom Wake Word Model**:
   - Create at: https://console.picovoice.ai/
   - Train for the phrase "Puerto-ocho"
   - Download the Raspberry Pi model

## Notes

- These models are required for the wake word detection to work
- Make sure to use the correct access key in your environment variables
- The models are specific to the target platform (Raspberry Pi)
