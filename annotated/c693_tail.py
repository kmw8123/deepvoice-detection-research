# 보관용 주석 사본. 원본은 ../src/c693_tail.py이며 실행 AST는 원본과 동일하게 유지한다.
# 별도 tail의 상류 라이선스/비상업 조건은 ../THIRD_PARTY_NOTICES.md를 함께 읽어야 한다.
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
    # 원 DF의 마지막 Conformer block + fc5를 복사해 학습한 43,137,922개 파라미터.
    # 비싼 1B encoder를 추가 복제/재학습하는 것이 아니다.
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
        # CLS 위치만 사용한다. 시간축 mean pooling으로 바꾸면 다른 모델이 된다.
        return self.fc5(features[:, 0, :])


def load_tail(path, device):
    """Load the pinned local C688 state_dict strictly with weights_only=True."""
    # 정확한 최종128 체크포인트만 허용한다. 새로운 후보/기타 크기의 가중치 자동 대체 없음.
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
    # 네 번째 Conformer block 직전 [B,202,1280]을 원 forward에서 한 번만 캡처한다.
    # 원 모델은 끝까지 실행해 외부 Voice용 원 logits를 만들고, tail은 File용 logits를 만든다.
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
        # 예외가 생겨도 hook을 제거하여 다음 파일에 상태가 누적되지 않도록 한다.
        hook.remove()
