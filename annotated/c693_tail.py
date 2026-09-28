# Annotated archive copy. I keep the executable AST identical to the original at ../src/c693_tail.py.
# See ../THIRD_PARTY_NOTICES.md for the separate tail's upstream license and noncommercial terms.
"""Frozen C688 tail, sharing one original DF-Arena forward per audio batch.

The caller provides the offline DF model in FP32 eval mode and puts batches
and the tail on the same device. A batch must contain windows of one file.
This module never changes the original model's weights or training mode.
"""

import hashlib
from pathlib import Path

import torch
from df_arena_1b.conformer import ConformerBlock


CHECKPOINT_SHA256 = "0281f889b4506af2f7d0d4280ba5f2b458e538a57dfcea1a020e112d1e968afc"
CHECKPOINT_BYTES = 172585774


class LastBlockAndHead(torch.nn.Module):
    # I copied and trained the original DF's final Conformer block + fc5: 43,137,922 parameters.
    # This does not duplicate or retrain the expensive 1B encoder.
    def __init__(self):
        super().__init__()
        self.block = ConformerBlock(
            dim=1280,
            dim_head=320,
            heads=4,
            ff_mult=4,
            conv_expansion_factor=2,
            conv_kernel_size=31,
        )
        self.fc5 = torch.nn.Linear(1280, 2)

    def forward(self, hidden):
        features, _ = self.block(hidden)
        # Use only the CLS position. Replacing this with temporal mean pooling would change the model.
        return self.fc5(features[:, 0, :])


def load_tail(path, device):
    """Load the pinned local C688 state_dict strictly with weights_only=True."""
    # Accept only the exact final update-128 checkpoint; do not substitute another candidate or weights of a different size.
    path = Path(path)
    if path.stat().st_size != CHECKPOINT_BYTES:
        raise ValueError(f"C688 checkpoint size mismatch: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != CHECKPOINT_SHA256:
        raise ValueError(f"C688 checkpoint SHA-256 mismatch: {path}")

    state = torch.load(path, map_location="cpu", weights_only=True)
    if not isinstance(state, dict) or not all(
        isinstance(value, torch.Tensor) for value in state.values()
    ):
        raise ValueError("C688 checkpoint must contain a tensor-only state_dict")
    if any(value.is_floating_point() and value.dtype != torch.float32 for value in state.values()):
        raise ValueError("C688 checkpoint floating tensors must be FP32")
    model = LastBlockAndHead().float()
    model.load_state_dict(state, strict=True)
    model.to(device=device, dtype=torch.float32).eval().requires_grad_(False)
    return model


def forward_shared(df_model, tail, batch):
    """Return original/C688 logits from one original forward and one saved-prefix tail.

    Inputs are FP32 [B, 64600], with B >= 1. Both models must already be in
    eval mode; refusing training mode preserves original BatchNorm buffers.
    The temporary hook is removed even when inference or validation fails.
    """
    if not isinstance(batch, torch.Tensor) or batch.ndim != 2:
        raise ValueError("DF batch must be a tensor with shape [B, 64600]")
    if batch.shape[0] < 1 or batch.shape[1] != 64600:
        raise ValueError(f"DF batch must have shape [B, 64600], got {tuple(batch.shape)}")
    if batch.dtype != torch.float32 or not torch.isfinite(batch).all().item():
        raise ValueError("DF batch must contain finite FP32 samples")
    for name, model in (("original DF", df_model), ("C688 tail", tail)):
        if any(module.training for module in model.modules()):
            raise ValueError(f"{name} must already be in eval mode")
        if any(parameter.dtype != torch.float32 for parameter in model.parameters()):
            raise ValueError(f"{name} parameters must be FP32")

    captured = []

    def capture_prefix(_module, args):
        captured.append(args[0].detach().clone())

    hook = df_model.backbone.conformer.encoder_blocks[3].register_forward_pre_hook(capture_prefix)
    # Capture [B,202,1280] immediately before the fourth Conformer block, once during the original forward pass.
    # The original model completes its forward pass for external Voice logits; the tail produces logits for File.
    try:
        with torch.no_grad(), torch.autocast(device_type=batch.device.type, enabled=False):
            original_logits = df_model(input_values=batch)["logits"]
            if len(captured) != 1:
                raise RuntimeError(f"Expected one DF prefix capture, got {len(captured)}")
            hidden = captured[0]
            expected_hidden = (batch.shape[0], 202, 1280)
            if tuple(hidden.shape) != expected_hidden or hidden.dtype != torch.float32:
                raise RuntimeError(f"Expected FP32 prefix {expected_hidden}, got {hidden.dtype} {tuple(hidden.shape)}")
            if not torch.isfinite(hidden).all().item():
                raise RuntimeError("DF prefix contains non-finite values")
            learned_logits = tail(hidden)
            for name, logits in (("original", original_logits), ("C688", learned_logits)):
                if tuple(logits.shape) != (batch.shape[0], 2) or logits.dtype != torch.float32:
                    raise RuntimeError(f"{name} logits must be FP32 [B, 2]")
                if not torch.isfinite(logits).all().item():
                    raise RuntimeError(f"{name} logits contain non-finite values")
            return original_logits.float(), learned_logits.float()
    finally:
        # Remove the hook even on an exception, preventing state from accumulating across files.
        hook.remove()
