"""Verify DIS geometry across consecutive pass-through layers."""

from pathlib import Path

import flopy
import numpy as np
import pytest
from framework import TestFramework

cases = ["dis_idm_pass"]


def build_models(case_index: int, test: TestFramework):
    """Build a column with two active cells separated by pass-through cells."""
    name = cases[case_index]
    simulation = flopy.mf6.MFSimulation(
        sim_name=name,
        version="mf6",
        exe_name="mf6",
        sim_ws=test.workspace,
    )
    flopy.mf6.ModflowTdis(
        simulation,
        time_units="DAYS",
        nper=1,
        perioddata=[(1.0, 1, 1.0)],
    )
    flopy.mf6.ModflowIms(
        simulation,
        print_option="SUMMARY",
        outer_dvclose=1.0e-9,
        inner_dvclose=1.0e-9,
    )

    groundwater_model = flopy.mf6.ModflowGwf(
        simulation,
        modelname=name,
        save_flows=True,
    )

    # the pass-through layer bottoms deliberately cross the lower active-cell
    # bottom. only the nearest active layer defines the lower cell's top.
    flopy.mf6.ModflowGwfdis(
        groundwater_model,
        nlay=4,
        nrow=1,
        ncol=1,
        top=10.0,
        botm=[6.0, 2.0, -2.0, 0.0],
        idomain=[1, -1, -1, 1],
    )
    flopy.mf6.ModflowGwfic(
        groundwater_model,
        strt=[8.0, 0.0, 0.0, 3.0],
    )
    flopy.mf6.ModflowGwfnpf(
        groundwater_model,
        icelltype=0,
        k=1.0,
        save_flows=True,
    )
    flopy.mf6.ModflowGwfchd(
        groundwater_model,
        stress_period_data=[((0, 0, 0), 8.0), ((3, 0, 0), 3.0)],
    )
    flopy.mf6.ModflowGwfoc(
        groundwater_model,
        head_filerecord=f"{name}.hds",
        budget_filerecord=f"{name}.cbc",
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
    )

    return simulation, None


def check_output(case_index: int, test: TestFramework) -> None:
    """Confirm the heads and vertical flow produced by the active-cell geometry."""
    head_path = Path(test.workspace) / f"{cases[case_index]}.hds"
    heads = flopy.utils.HeadFile(head_path, precision="double").get_data()

    np.testing.assert_allclose(
        heads[[0, 3], 0, 0],
        np.array([8.0, 3.0]),
        rtol=0.0,
        atol=1.0e-12,
    )

    # the fixed heads differ by five length units. the expected unit flow
    # proves that the lower cell uses the upper active-cell bottom as its top.
    budget_path = Path(test.workspace) / f"{cases[case_index]}.cbc"
    flow_ja_face = flopy.utils.CellBudgetFile(
        budget_path,
        precision="double",
    ).get_data(text="FLOW-JA-FACE")[-1]
    np.testing.assert_allclose(
        flow_ja_face.ravel(),
        np.array([0.0, -1.0, 0.0, 1.0]),
        rtol=0.0,
        atol=1.0e-12,
    )


@pytest.mark.parametrize("case_index, name", list(enumerate(cases)))
def test_mf6model(
    case_index: int,
    name: str,
    function_tmpdir: Path,
    targets: dict[str, Path],
) -> None:
    """Run the consecutive pass-through-layer regression case."""
    test = TestFramework(
        name=name,
        workspace=function_tmpdir,
        build=lambda current_test: build_models(case_index, current_test),
        check=lambda current_test: check_output(case_index, current_test),
        targets=targets,
    )
    test.run()
