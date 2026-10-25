# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM-Omni project
"""Reproduce configuration findings without importing the vLLM/GPU runtime.

Temporary investigation aid, not a production fix or a runtime test.
Requires Python >= 3.11 and Pydantic 2. Pass the repository root and the
installed vLLM config/utils.py source used for the configuration decorator.
"""

from __future__ import annotations

import argparse
import ast
import json
import platform
from collections.abc import Callable, Mapping
from dataclasses import dataclass as std_dataclass, fields
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar, dataclass_transform

import pydantic
from pydantic import ConfigDict, Field as PydanticField, model_validator
from pydantic.dataclasses import dataclass as pyd_dataclass
from typing_extensions import Self

ConfigT = TypeVar("ConfigT")


def execute_nodes(nodes: list[ast.stmt], path: Path, namespace: dict[str, Any]) -> None:
    # Keep original source definitions, including the production validators.
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)


def investigate(repo_root: Path, vllm_utils: Path) -> dict[str, Any]:
    utility_namespace = dict(globals())
    utility_namespace["dataclass"] = pyd_dataclass
    utility_nodes = ast.parse(vllm_utils.read_text()).body
    decorator = next(
        node
        for node in utility_nodes
        if isinstance(node, ast.FunctionDef) and node.name == "config" and len(node.body) > 1
    )
    execute_nodes([decorator], vllm_utils, utility_namespace)
    namespace = dict(globals())
    namespace["config"] = utility_namespace["config"]
    namespace["dataclass"] = std_dataclass
    config_path = repo_root / "vllm_omni/diffusion/data.py"
    production_class = next(
        node
        for node in ast.parse(config_path.read_text()).body
        if isinstance(node, ast.ClassDef) and node.name == "DiffusionParallelConfig"
    )
    execute_nodes([production_class], config_path, namespace)

    helper_path = repo_root / "tests/model_tests/diffusion/config_types.py"
    helper_nodes = []
    for node in ast.parse(helper_path.read_text()).body:
        if isinstance(node, ast.ClassDef) and node.name == "DiffusionAccs":
            helper_nodes.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(
                isinstance(target, ast.Name)
                and target.id in {"ACC_PARALLEL_KWARGS", "ACC_DEVICE_COUNT_KEYS"}
                for target in targets
            ):
                helper_nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in {
            "get_required_device_count",
            "build_parallel_config_from_diff_accelerations",
        }:
            helper_nodes.append(node)
    execute_nodes(helper_nodes, helper_path, namespace)

    settings_path = repo_root / "tests/model_tests/diffusion/model_settings.py"
    settings = next(
        node.value
        for node in ast.parse(settings_path.read_text()).body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "DIFFUSION_TEST_SETTINGS" for target in node.targets)
    )
    model_count = len(settings.keys)
    group_count = 0
    mismatches = []
    for key, call in zip(settings.keys, settings.values):
        extras = next((kw.value for kw in call.keywords if kw.arg == "extra_test_groups"), None)
        group_count += 1 + (len(extras.elts) if extras is not None else 0)
        if extras is None:
            continue
        for group in extras.elts:
            names = [element.attr for element in group.elts]
            accelerations = [namespace["DiffusionAccs"][name] for name in names]
            config = namespace["build_parallel_config_from_diff_accelerations"](accelerations)
            helper_devices = namespace["get_required_device_count"](accelerations)
            world_size = config.world_size if config is not None else 1
            if helper_devices != world_size:
                mismatches.append(
                    {
                        "model": key.value,
                        "accelerations": names,
                        "helper_required_devices": helper_devices,
                        "production_world_size": world_size,
                    }
                )

    checks = []
    configurations = [
        ("TP2_CFG2", {"tensor_parallel_size": 2, "cfg_parallel_size": 2}),
        ("SP2_HSDP2", {"ulysses_degree": 2, "use_hsdp": True, "hsdp_shard_size": 2}),
        ("TP2_HSDP2", {"tensor_parallel_size": 2, "use_hsdp": True, "hsdp_shard_size": 2}),
        ("Ring2_AllGather2", {"ring_degree": 2, "allgather_degree": 2}),
    ]
    for label, kwargs in configurations:
        try:
            config = namespace["DiffusionParallelConfig"](**kwargs)
            checks.append({"configuration": label, "accepted": True, "world_size": config.world_size})
        except ValueError as error:
            checks.append({"configuration": label, "accepted": False, "error": str(error)})
    return {
        "scope": "isolated CPU AST execution; no complete imports, runtime, GPU, or model weights",
        "python": platform.python_version(),
        "pydantic": pydantic.__version__,
        "configured_models": model_count,
        "offline_configured_model_groups": group_count,
        "online_default_base_groups": model_count,
        "device_count_mismatches": mismatches,
        "config_checks": checks,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--vllm-utils", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(investigate(args.repo_root, args.vllm_utils), ensure_ascii=False, indent=2))
