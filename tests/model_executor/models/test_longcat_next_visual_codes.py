# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM-Omni project

import pytest
import torch

from tests.model_executor.models.test_longcat_next_talker_mtp import (
    HIDDEN,
    VISUAL_OFFSET,
    M,
    _visual_state,
)
from tests.model_executor.models.test_longcat_next_talker_mtp import (
    model as model,
)
from vllm_omni.model_executor.models.longcat_next.longcat_next_utils import (
    IMG_NEWLINE_TOKEN_ID,
    IMG_PAD_TOKEN_ID,
)

pytestmark = [pytest.mark.core_model, pytest.mark.cpu]


def _call_visual(model, cfg, token=IMG_PAD_TOKEN_ID, do_sample=False):
    req_ids = ["parent"]
    if cfg:
        req_ids.append("parent__cfg_visual")
    for req_id in req_ids:
        model._visual_gen[req_id] = _visual_state(ext_id=token)
    batch = len(req_ids)
    return M.talker_mtp(
        model,
        input_ids=torch.full((batch,), token),
        inputs_embeds=torch.zeros(batch, HIDDEN),
        last_talker_hidden=torch.zeros(batch, HIDDEN),
        text_step=torch.zeros(batch, HIDDEN),
        req_ids=req_ids,
        do_sample=do_sample,
        top_k=1,
    )


@pytest.mark.parametrize("cfg", [False, True], ids=["plain", "cfg"])
@pytest.mark.parametrize("do_sample", [False, True], ids=["greedy", "sample"])
def test_all_visual_levels_exclude_sentinel(model, cfg, do_sample):
    sizes = model.visual_codebook_sizes

    def visual_head(hidden, tokens, embeddings, level):
        logits = torch.full((1, sizes[level] + 1), -1000.0)
        logits[0, sizes[level]] = 1000.0
        logits[0, 7] = 100.0
        return logits

    model.visual_head = visual_head
    _, codes = _call_visual(model, cfg, do_sample=do_sample)
    assert torch.equal(codes, torch.full_like(codes, 7))


@pytest.mark.parametrize("cfg", [False, True], ids=["plain", "cfg"])
@pytest.mark.parametrize("winner", [0, 7], ids=["zero", "nonzero"])
@pytest.mark.parametrize("newline", [False, True], ids=["pixel", "newline"])
def test_visual_feedback_keeps_zero_and_discards_newline(model, cfg, winner, newline):
    sizes = model.visual_codebook_sizes

    def visual_head(hidden, tokens, embeddings, level):
        logits = torch.full((1, sizes[level]), -1000.0)
        logits[0, winner] = 100.0
        return logits

    def embed_tokens(ids):
        return (ids >= VISUAL_OFFSET).to(torch.float32).unsqueeze(-1).expand(*ids.shape, HIDDEN)

    model.visual_head = visual_head
    model.model.embed_tokens = embed_tokens
    token = IMG_NEWLINE_TOKEN_ID if newline else IMG_PAD_TOKEN_ID
    embeds, codes = _call_visual(model, cfg, token=token)
    assert torch.equal(codes, torch.full_like(codes, -1 if newline else winner))
    assert torch.equal(embeds, torch.full_like(embeds, 0.0 if newline else 8.0))
