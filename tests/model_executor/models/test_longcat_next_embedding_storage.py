# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM-Omni project

import pytest
import torch
from torch import nn

from vllm_omni.model_executor.models.longcat_next.modeling_longcat_next import LongcatNextForCausalLM as M

pytestmark = [pytest.mark.core_model, pytest.mark.cpu]


class _Backbone(nn.Module):
    def __init__(self, dtype):
        super().__init__()
        self.dtype = dtype

    def embed_tokens(self, ids):
        return (ids[:, None] + torch.arange(4)[None, :] / 8).to(self.dtype)


class _Model(nn.Module):
    _ensure_replicated_audio_code_embedding = M._ensure_replicated_audio_code_embedding
    _ensure_audio_code_embed_module = M._ensure_audio_code_embed_module
    _ensure_replicated_visual_code_embedding = M._ensure_replicated_visual_code_embedding
    _ensure_visual_code_embed_module = M._ensure_visual_code_embed_module

    def __init__(self, dtype):
        super().__init__()
        self.dtype = dtype
        self.audio_codebook_sizes = [3, 2]
        self.visual_codebook_sizes = [5, 4]
        self.register_buffer("audio_offset_vals", torch.tensor([10, 13]))
        self.register_buffer("visual_offset_vals", torch.tensor([20, 25]))
        self.model = _Backbone(dtype)


@pytest.mark.parametrize("modality", ["audio", "visual"])
@pytest.mark.parametrize("dtype", [torch.float32, torch.bfloat16])
def test_head_embedding_shares_frozen_storage_with_feedback(modality, dtype):
    model = _Model(dtype)
    ensure_rows = getattr(model, f"_ensure_replicated_{modality}_code_embedding")
    ensure_module = getattr(model, f"_ensure_{modality}_code_embed_module")
    rows = ensure_rows(torch.device("cpu"))
    head_embedding = ensure_module(torch.device("cpu"))
    assert head_embedding.weight.untyped_storage().data_ptr() == rows.untyped_storage().data_ptr()
    assert head_embedding.weight.requires_grad is False
    assert head_embedding.weight.dtype == dtype
    ids = torch.arange(rows.shape[0])
    torch.testing.assert_close(head_embedding(ids), rows, rtol=0, atol=0)
    assert ensure_module(torch.device("cpu")) is head_embedding
    assert ensure_rows(torch.device("cpu")) is rows
    storages = {t.untyped_storage().data_ptr(): t.untyped_storage().nbytes() for t in (rows, head_embedding.weight)}
    assert sum(storages.values()) == rows.numel() * rows.element_size()
