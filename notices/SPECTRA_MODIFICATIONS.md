# Spectra-AASIST3 inference modifications

Source model: `lab260/Spectra-AASIST3`  
Pinned revision: `bc0ded888080ddad493177bb53aa6f5b95219d7c`

The upstream `model.py` constructs its XLS-R-300M encoder with
`Wav2Vec2Model.from_pretrained("facebook/wav2vec2-xls-r-300m")`, even though
the released `model.safetensors` contains the complete encoder state.

For offline DACON inference, this copy:

1. constructs `Wav2Vec2Model` from the bundled upstream config pinned at
   `facebook/wav2vec2-xls-r-300m@1a640f32ac3e39899438a2931f9924c02f080a54`;
2. removes `PyTorchModelHubMixin`, which is only a network/download helper;
3. leaves the network layers and checkpoint parameter names unchanged; and
4. requires a strict safetensors load before inference.

No training, fine-tuning, calibration on DACON data, or parameter update is
performed.
