"""Tooltips for table view columns."""

import numpy as np

# Tooltips
_HEADER_TIPS: dict[str, dict[str, str]] = {}
_CELL_TIPS: dict[str, dict[str, str]] = {}


def register_tips(
    table: str,
    header: dict[str, str] | None = None,
    cell: dict[str, str] | None = None,
) -> None:
    """Register tooltips for a given table."""
    if header:
        _HEADER_TIPS.setdefault(table, {}).update(header)
    if cell:
        _CELL_TIPS.setdefault(table, {}).update(cell)


# Measurement Tooltips
register_tips(
    "measurement",
    header={
        "observableId": "ID from Observables; the output being measured.",
        "preequilibrationConditionId": "Condition for preequilibration; empty = none.",
        "simulationConditionId": "Condition ID used for simulation.",
        "time": "Time in SBML units; number or 'inf' (steady state).",
        "measurement": "Measured value; same units/scale as model output.",
        "observableParameters": "Override placeholder params; ';'-separated values/names; empty if none.",
        "noiseParameters": "Std dev σ as value or name; NaN if σ is modeled.",
        "datasetId": "Dataset grouping ID (for plotting).",
        "replicateId": "Replicate label within datasetId.",
    },
    cell={
        "observableId": "Must exist in Observables.",
        "preequilibrationConditionId": "Condition ID or empty for no preeq.",
        "simulationConditionId": "Condition ID from Conditions.",
        "time": "e.g. 0, 5, 10 or 'inf' for steady state.",
        "measurement": "Numeric observed value.",
        "observableParameters": "Match placeholders; provide n ';'-separated values/names.",
        "noiseParameters": "Sigma value or parameter name; NaN if modeled.",
        "datasetId": "Optional dataset ID to group points.",
        "replicateId": "Optional replicate tag within dataset.",
    },
)

# Observable Tooltips
register_tips(
    "observable",
    header={
        "observableId": "Unique ID; letters, digits, underscores; not starting with digit. Referenced in Measurements.",
        "observableName": "Optional display name; not used for identification.",
        "observableFormula": "Observation function as text formula. May use SBML symbols or parameters from parameter table. Can introduce placeholder parameters observableParameter{n}_{observableId}.",
        "observableTransformation": "Transformation applied in objective; one of lin, log, log10. Default: lin.",
        "noiseFormula": "Noise model formula or numeric σ. May include noiseParameter{n}_{observableId}. Must be overridden in Measurement table if present.",
        "noiseDistribution": "Noise distribution type: normal (σ) or laplace (scale). Default: normal.",
    },
    cell={
        "observableId": "Identifier; must be valid and unique. Used in Measurement table.",
        "observableName": "Optional label for output/plots.",
        "observableFormula": "E.g. a species ID, assignment rule, or formula with parameters.",
        "observableTransformation": "Choose: lin, log, or log10.",
        "noiseFormula": "Numeric σ or formula with noiseParameter{n}_{observableId}.",
        "noiseDistribution": "normal (σ as std dev) or laplace (σ as scale).",
    },
)

# Parameter Tooltips
register_tips(
    "parameter",
    header={
        "parameterId": "Unique ID; must match SBML parameter, condition override, or observable/noise parameter.",
        "parameterName": "Optional label for plotting; may differ from SBML name.",
        "parameterScale": "Scale for estimation: lin, log, or log10.",
        "lowerBound": "Lower bound (linear space). Optional if estimate==0.",
        "upperBound": "Upper bound (linear space). Optional if estimate==0.",
        "nominalValue": "Value if not estimated (estimate==0). Linear space.",
        "estimate": "1 = estimated, 0 = fixed.",
        "initializationPriorType": "Prior for sampling initial points. Default: parameterScaleUniform.",
        "initializationPriorParameters": "Parameters for initialization prior; ';'-separated; numeric.",
        "objectivePriorType": "Prior type used in objective function.",
        "objectivePriorParameters": "Parameters for objective prior; ';'-separated; numeric.",
    },
    cell={
        "parameterId": "Must match SBML/condition/observable/noise parameter ID.",
        "parameterName": "Optional descriptive name.",
        "parameterScale": "Choose lin, log, or log10.",
        "lowerBound": "Numeric lower bound (linear space).",
        "upperBound": "Numeric upper bound (linear space).",
        "nominalValue": "Numeric value if not estimated.",
        "estimate": "0 = fixed, 1 = estimated.",
        "initializationPriorType": "E.g., uniform, normal, laplace, logNormal, parameterScaleUniform…",
        "initializationPriorParameters": "Numeric parameters for init prior; e.g., mean;stddev.",
        "objectivePriorType": "Prior type for optimization objective.",
        "objectivePriorParameters": "Numeric parameters for objective prior.",
    },
)

# Condition Tooltips
register_tips(
    "condition",
    header={
        "conditionId": "Unique ID; letters/digits/underscores; not starting with digit. Referenced by Measurements.",
        "conditionName": "Optional human-readable name for reports/plots.",
        "*": "User-defined column. Needs to be SBML ID column: parameter, species, or compartment.",
    },
    cell={
        "conditionId": "Enter a valid, unique identifier.",
        "conditionName": "Optional label.",
        "*": "User-defined column. Provide numeric value or SBML/parameter ID. "
        "Species IDs = initial amount/concentration (NaN = keep preeq/initial). "
        "Compartment IDs = initial size.",
    },
)

register_tips(
    "visualization",
    header={
        "plotId": "Plot ID; datasets with same ID share axes.",
        "plotName": "Optional plot display name.",
        "plotTypeSimulation": "LinePlot | BarPlot | ScatterPlot. Default: LinePlot.",
        "plotTypeData": "MeanAndSD | MeanAndSEM | replicate | provided. Default: MeanAndSD.",
        "datasetId": "Dataset grouping ID from Measurements (optional).",
        "xValues": "Independent variable: 'time' (default) or parameter/state ID.",
        "xOffset": "Offset added to x values (default 0).",
        "xLabel": "X-axis label; defaults to xValues.",
        "xScale": "lin | log | log10 | order (only with LinePlot). Default: lin.",
        "yValues": "Observable ID to plot on Y.",
        "yOffset": "Offset added to y values (default 0).",
        "yLabel": "Y-axis label; defaults to yValues.",
        "yScale": "lin | log | log10. Default: lin.",
        "legendEntry": "Legend name; defaults to datasetId.",
    },
    cell={
        "plotId": "Required; same ID -> same axes.",
        "plotName": "Optional human-readable name.",
        "plotTypeSimulation": "Choose: LinePlot, BarPlot, or ScatterPlot.",
        "plotTypeData": "Choose: MeanAndSD, MeanAndSEM, replicate, or provided.",
        "datasetId": "Optional dataset ID to include in this plot.",
        "xValues": "Use 'time' or a parameter/state ID.",
        "xOffset": "Numeric x offset (e.g., 0).",
        "xLabel": "Custom X label (optional).",
        "xScale": "lin, log, log10, or order (LinePlot only).",
        "yValues": "Observable ID to plot on Y.",
        "yOffset": "Numeric y offset (e.g., 0).",
        "yLabel": "Custom Y label (optional).",
        "yScale": "lin, log, or log10.",
        "legendEntry": "Legend text; else datasetId is used.",
    },
)

_default_tip = ("User-defined column; no specific structure enforced.",)


def header_tip(table: str, column: str) -> str:
    """Get the tooltip for a given table header."""
    if table == "simulation":
        if column == "simulation":
            return "Simulations of the model at measurement time points."
        table = "measurement"
    return _HEADER_TIPS.get(table, {}).get(column) or _default_tip


def cell_tip(table: str, column: str) -> str:
    """Get the tooltip for a given table cell."""
    if table == "simulation":
        if column == "simulation":
            return "Simulation result at the specified time point."
        table = "measurement"
    return _CELL_TIPS.get(table, {}).get(column) or _default_tip


# SBML/Antimony View Tooltips
SBML_VIEW_TOOLTIP = (
    "<b>SBML (XML) view</b><br>"
    "• Edit or paste valid SBML.<br>"
    "• Use <i>Forward → Antimony</i> to sync.<br>"
    "• Some constructs may not round-trip."
)

ANTIMONY_VIEW_TOOLTIP = (
    "<b>Antimony view</b><br>"
    "• Human-readable model syntax.<br>"
    "• Use <i>Forward → SBML</i> to convert.<br>"
    "• Check the logger for syntax/convert errors."
)

MEAS_TABLE_TOOLTIP = (
    "<b>Measurement table</b><br>"
    "• One row = one data point.<br>"
    "• Specify observable, time, and conditions.<br>"
    "• Optionally override observable/noise parameters."
)

OBS_TABLE_TOOLTIP = (
    "<b>Observable table</b><br>"
    "• Map model outputs to measurements.<br>"
    "• Define formulas, transformation, and noise model."
)

PAR_TABLE_TOOLTIP = (
    "<b>Parameter table</b><br>"
    "• Define parameters and whether they are estimated (0/1).<br>"
    "• Bounds in linear space; optional priors."
)

COND_TABLE_TOOLTIP = (
    "<b>Condition table</b><br>"
    "• Define condition IDs and names.<br>"
    "• User-defined SBML ID columns override parameters/species initial "
    "states (NaN keeps preeq/initial)."
)

VIS_TABLE_TOOLTIP = (
    "<b>Visualization table</b><br>"
    "• Group datasets with <code>plotId</code>.<br>"
    "• Choose plot/data types; set axes labels/scales/offsets."
)

SIM_TABLE_TOOLTIP = (
    "<b>Simulation table</b><br>"
    "• Simulation results at measurement time points."
)

INFO_TOOLTIP = (
    "<b>Info panel</b><br>"
    "• Messages, warnings, and logs from operations.<br>"
    "• Links to documentation when available."
)

DATA_PLOT_TOOLTIP = (
    "<b>Data plot</b><br>"
    "• Visualizes simulations and measurements.<br>"
    "• Can also group by condition/observable."
)

DATA_TABLES_TAB_TOOLTIP = (
    "<b>Data Tables</b><br>"
    "• Edit PEtab tables: Measurement, Observable, Parameter, Condition,"
    " Visualization.<br>"
    "• Hover headers for definitions;"
    " use toolbar to add/remove rows and import/export."
)

SBML_MODEL_TAB_TOOLTIP = (
    "<b>SBML Model</b><br>"
    "• Edit SBML (XML) and Antimony side-by-side.<br>"
    "• Use <i>Forward Changes</i> buttons to sync; see logger for errors."
)
