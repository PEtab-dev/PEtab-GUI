"""What's This? Dialog desciptions of the widgets."""
WHATS_THIS = {
  "tabs": {
    "data_tables": (
      "<html><b>Data Tables</b><br>"
      "<ul>"
      "<li>Edit PEtab tables: Measurement, Observable, Parameter, Condition, Visualization.</li>"
      "<li>Hover headers for definitions; right-click for context actions.</li>"
      "<li>Keep IDs consistent across tables (e.g., <code>observableId</code>, condition IDs).</li>"
      "<li>Import/export to manage files; validation highlights issues.</li>"
      "</ul></html>"
    ),
    "sbml_model": (
      "<html><b>SBML Model</b><br>"
      "<ul>"
      "<li>Edit SBML (XML) and Antimony side-by-side.</li>"
      "<li>Use the <i>Forward Changes</i> buttons to convert/sync between views.</li>"
      "<li>Errors and warnings appear in the logger panel below.</li>"
      "<li>Some constructs may not round-trip perfectly; keep the canonical SBML copy.</li>"
      "</ul></html>"
    ),
  },
  "sbml_view": {
    "sbml_editor": (
      "<html><b>SBML editor (XML)</b><br>"
      "<ul>"
      "<li>Paste or edit valid SBML (L2/L3); keep namespaces intact.</li>"
      "<li>Click <i>Forward → Antimony</i> to generate Antimony.</li>"
      "<li>Prefer this pane for full SBML feature coverage.</li>"
      "<li>Conversion issues are reported in the logger.</li>"
      "</ul></html>"
    ),
    "antimony_editor": (
      "<html><b>Antimony editor</b><br>"
      "<ul>"
      "<li>Human-readable model syntax compiled to SBML.</li>"
      "<li>Click <i>Forward → SBML</i> to regenerate XML.</li>"
      "<li>Use for quick edits; verify semantics after conversion.</li>"
      "<li>Syntax/convert errors will appear in the logger.</li>"
      "</ul></html>"
    ),
  },
  "tables": {
    "measurement": {
      "table": (
        "<html><b>Measurement table</b><br>"
        "<ul>"
        "<li>Each row is a data point with time, value, and linked IDs.</li>"
        "<li><code>observableId</code> must exist in <b>Observable</b>; "
        "condition IDs must exist in <b>Condition</b>.</li>"
        "<li>Use <code>'inf'</code> for steady-state times.</li>"
        "<li>Override placeholders <code>observableParameter{n}_{observableId}</code> "
        "and noise parameters <code>noiseParameter{n}_{observableId}</code> when defined.</li>"
        "</ul></html>"
      ),
      "columns": {
        "observableId": (
          "<html><ul>"
          "<li>Reference to an observable defined in the Observable table.</li>"
          "<li>Must match an existing <code>observableId</code>.</li>"
          "</ul></html>"
        ),
        "preequilibrationConditionId": (
          "<html><ul>"
          "<li>Condition used for pre-equilibration; empty = none.</li>"
          "<li>Must be a valid condition ID if provided.</li>"
          "</ul></html>"
        ),
        "simulationConditionId": (
          "<html><ul>"
          "<li>Condition used for simulation parameters (required).</li>"
          "<li>Must be a valid condition ID.</li>"
          "</ul></html>"
        ),
        "time": (
          "<html><ul>"
          "<li>Numeric time in SBML units, or <code>'inf'</code> for steady state.</li>"
          "<li>Use a consistent unit system across data and model.</li>"
          "</ul></html>"
        ),
        "measurement": (
          "<html><ul>"
          "<li>Observed numeric value in the same scale/units as the model output.</li>"
          "<li>Leave blank for missing values if supported by your workflow.</li>"
          "</ul></html>"
        ),
        "observableParameters": (
          "<html><ul>"
          "<li>Overrides for placeholders defined in the observable formula.</li>"
          "<li>Provide <code>n</code> semicolon-separated values/names for "
          "<code>observableParameter{n}_{observableId}</code>; empty if none.</li>"
          "</ul></html>"
        ),
        "noiseParameters": (
          "<html><ul>"
          "<li>Noise std-dev (or parameter names); <code>NaN</code> if σ is a model parameter.</li>"
          "<li>Same rules as <code>observableParameters</code> for lists and naming.</li>"
          "</ul></html>"
        ),
        "datasetId": (
          "<html><ul>"
          "<li>Grouping key for plotting (datasets share style/axes).</li>"
          "<li>Optional; defaults to per-row if omitted.</li>"
          "</ul></html>"
        ),
        "replicateId": (
          "<html><ul>"
          "<li>Label to distinguish replicates within a dataset.</li>"
          "<li>Enables error bars/replicate plotting modes.</li>"
          "</ul></html>"
        ),
      },
    },
    "simulation": {
      "table": (
        "<html><b>Simulation table</b><br>"
        "<ul>"
        "<li>Holds simulated outputs aligned to measurement definitions.</li>"
        "<li>Same IDs as Measurement (observable/conditions/time) for comparison.</li>"
        "<li>Populated by simulator/export; typically read-only.</li>"
        "</ul></html>"
      ),
      "columns": {
        "observableId": (
          "<html><ul>"
          "<li>Observable whose simulation is reported.</li>"
          "<li>Must match an <code>observableId</code> in Observable.</li>"
          "</ul></html>"
        ),
        "preequilibrationConditionId": (
          "<html><ul>"
          "<li>Preequilibration condition used during simulation; empty = none.</li>"
          "<li>Must be a valid condition ID if set.</li>"
          "</ul></html>"
        ),
        "simulationConditionId": (
          "<html><ul>"
          "<li>Condition used to set simulation parameters (required).</li>"
          "<li>Must be a valid condition ID.</li>"
          "</ul></html>"
        ),
        "time": (
          "<html><ul>"
          "<li>Time point for the simulated value (numeric or <code>'inf'</code>).</li>"
          "<li>Use same units as the model.</li>"
          "</ul></html>"
        ),
        "simulation": (
          "<html><ul>"
          "<li>Simulated numeric value (same scale/units as measurement).</li>"
          "<li>Used for plotting and residuals.</li>"
          "</ul></html>"
        ),
        "observableParameters": (
          "<html><ul>"
          "<li>Parameters used to evaluate observable placeholders, if applicable.</li>"
          "<li>Semicolon-separated values/names; mirrors Measurement rules.</li>"
          "</ul></html>"
        ),
        "noiseParameters": (
          "<html><ul>"
          "<li>Noise parameters applied for simulation/plotting modes.</li>"
          "<li>Numeric values or names; may be empty.</li>"
          "</ul></html>"
        ),
        "datasetId": (
          "<html><ul>"
          "<li>Dataset grouping to match plotted series.</li>"
          "<li>Optional; align with Measurement for overlays.</li>"
          "</ul></html>"
        ),
        "replicateId": (
          "<html><ul>"
          "<li>Replicate label, if simulations are per-replicate.</li>"
          "<li>Usually empty unless replicates are simulated explicitly.</li>"
          "</ul></html>"
        ),
      },
    },
    "observable": {
      "table": (
        "<html><b>Observable table</b><br>"
        "<ul>"
        "<li>Defines how model states/expressions map to measured outputs.</li>"
        "<li>May introduce placeholders <code>observableParameter{n}_{observableId}</code> "
        "that are overridden per-measurement.</li>"
        "<li>Noise model can be numeric σ or a formula; distribution optional.</li>"
        "</ul></html>"
      ),
      "columns": {
        "observableId": (
          "<html><ul>"
          "<li>Unique identifier (letters/digits/underscores; not starting with a digit).</li>"
          "<li>Referenced by <code>measurement.observableId</code>.</li>"
          "</ul></html>"
        ),
        "observableName": (
          "<html><ul>"
          "<li>Optional display name for reports/plots.</li>"
          "<li>Not used for identification.</li>"
          "</ul></html>"
        ),
        "observableFormula": (
          "<html><ul>"
          "<li>Expression using SBML symbols/parameters (e.g., species ID).</li>"
          "<li>May define <code>observableParameter{n}_{observableId}</code> placeholders.</li>"
          "</ul></html>"
        ),
        "observableTransformation": (
          "<html><ul>"
          "<li>Transformation for objective: <code>lin</code>, <code>log</code>, or <code>log10</code>.</li>"
          "<li>Defaults to <code>lin</code>; data and outputs assumed linear if not set.</li>"
          "</ul></html>"
        ),
        "noiseFormula": (
          "<html><ul>"
          "<li>Numeric σ (implies normal) or formula for complex noise.</li>"
          "<li>May include <code>noiseParameter{n}_{observableId}</code>; "
          "values provided in Measurement.</li>"
          "</ul></html>"
        ),
        "noiseDistribution": (
          "<html><ul>"
          "<li><code>normal</code> (σ = std dev) or <code>laplace</code> (σ = scale).</li>"
          "<li>Log-variants via <code>observableTransformation</code> = log/log10.</li>"
          "</ul></html>"
        ),
      },
    },
    "parameter": {
      "table": (
        "<html><b>Parameter table</b><br>"
        "<ul>"
        "<li>Declares parameters, estimation flag, and bounds (linear space).</li>"
        "<li><code>parameterId</code> must match SBML or overrides used elsewhere.</li>"
        "<li>Optional priors for initialization and/or objective.</li>"
        "</ul></html>"
      ),
      "columns": {
        "parameterId": (
          "<html><ul>"
          "<li>Must match an SBML parameter, a condition override, or names used in measurements.</li>"
          "<li>Unique within this table.</li>"
          "</ul></html>"
        ),
        "parameterName": (
          "<html><ul>"
          "<li>Optional display name for plots/reports.</li>"
          "<li>May differ from SBML name.</li>"
          "</ul></html>"
        ),
        "parameterScale": (
          "<html><ul>"
          "<li>Estimation scale: <code>lin</code>, <code>log</code>, or <code>log10</code>.</li>"
          "<li>Affects optimization scaling, not storage format.</li>"
          "</ul></html>"
        ),
        "lowerBound": (
          "<html><ul>"
          "<li>Numeric lower bound in <b>linear</b> space.</li>"
          "<li>Optional if <code>estimate==0</code>.</li>"
          "</ul></html>"
        ),
        "upperBound": (
          "<html><ul>"
          "<li>Numeric upper bound in <b>linear</b> space.</li>"
          "<li>Optional if <code>estimate==0</code>.</li>"
          "</ul></html>"
        ),
        "nominalValue": (
          "<html><ul>"
          "<li>Value used when fixed (<code>estimate==0</code>), in <b>linear</b> space.</li>"
          "<li>Optional otherwise.</li>"
          "</ul></html>"
        ),
        "estimate": (
          "<html><ul>"
          "<li><code>1</code> = estimated; <code>0</code> = fixed to nominal value.</li>"
          "<li>Controls inclusion in the optimization vector.</li>"
          "</ul></html>"
        ),
        "initializationPriorType": (
          "<html><ul>"
          "<li>Prior for initial point sampling (e.g., <code>uniform</code>, <code>normal</code>, "
          "<code>parameterScaleUniform</code>).</li>"
          "<li>Defaults to <code>parameterScaleUniform</code>.</li>"
          "</ul></html>"
        ),
        "initializationPriorParameters": (
          "<html><ul>"
          "<li>Semicolon-separated numeric parameters; default <code>lowerBound;upperBound</code>.</li>"
          "<li>Linear scale unless using parameter-scale priors.</li>"
          "</ul></html>"
        ),
        "objectivePriorType": (
          "<html><ul>"
          "<li>Prior contributing to the objective; same options as initialization prior.</li>"
          "<li>Optional; omit for unregularized fits.</li>"
          "</ul></html>"
        ),
        "objectivePriorParameters": (
          "<html><ul>"
          "<li>Semicolon-separated numeric parameters; see initialization prior for formats.</li>"
          "<li>Scale rules mirror the chosen prior type.</li>"
          "</ul></html>"
        ),
      },
    },
    "condition": {
      "table": (
        "<html><b>Condition table</b><br>"
        "<ul>"
        "<li>Defines simulation/experimental conditions referenced by other tables.</li>"
        "<li>User-defined columns must be SBML IDs (parameter/species/compartment).</li>"
        "<li>Species values act as initial conditions;</li>"
        "</ul></html>"
      ),
      "columns": {
        "conditionId": (
          "<html><ul>"
          "<li>Unique identifier (letters/digits/underscores; not starting with a digit).</li>"
          "<li>Referenced by Measurement and Simulation.</li>"
          "</ul></html>"
        ),
        "conditionName": (
          "<html><ul>"
          "<li>Optional human-readable name for reports/plots.</li>"
          "<li>Does not affect model execution.</li>"
          "</ul></html>"
        ),
        "*": (
          "<html><ul>"
          "<li>User-defined column. Must be an SBML ID: parameter, species, or compartment.</li>"
          "<li>Numbers or IDs allowed; species = initial amount/concentration "
          "(<code>NaN</code> keeps preeq/initial), compartments = initial size.</li>"
          "</ul></html>"
        ),
      },
    },
    "visualization": {
      "table": (
        "<html><b>Visualization table</b><br>"
        "<ul>"
        "<li>Groups datasets into plots and configures axes/scales.</li>"
        "<li><code>plotId</code> collects series into the same axes.</li>"
        "<li>Choose simulation/data types; set labels and offsets.</li>"
        "</ul></html>"
      ),
      "columns": {
        "plotId": (
          "<html><ul>"
          "<li>Plot grouping key; identical IDs share the same axes.</li>"
          "<li>Required for multi-series plots.</li>"
          "</ul></html>"
        ),
        "plotName": (
          "<html><ul>"
          "<li>Optional display name for the plot.</li>"
          "<li>Used in UIs/exports; not an ID.</li>"
          "</ul></html>"
        ),
        "plotTypeSimulation": (
          "<html><ul>"
          "<li><code>LinePlot</code> | <code>BarPlot</code> | <code>ScatterPlot</code>.</li>"
          "<li>Default is <code>LinePlot</code>.</li>"
          "</ul></html>"
        ),
        "plotTypeData": (
          "<html><ul>"
          "<li><code>MeanAndSD</code> | <code>MeanAndSEM</code> | <code>replicate</code> | <code>provided</code>.</li>"
          "<li>Default is <code>MeanAndSD</code>.</li>"
          "</ul></html>"
        ),
        "datasetId": (
          "<html><ul>"
          "<li>Includes datasets (from Measurement) in this plot.</li>"
          "<li>Optional; multiple IDs → multiple series.</li>"
          "</ul></html>"
        ),
        "xValues": (
          "<html><ul>"
          "<li>Independent variable: <code>time</code> (default) or parameter/state ID.</li>"
          "<li>Values appear as x-axis ticks.</li>"
          "</ul></html>"
        ),
        "xOffset": (
          "<html><ul>"
          "<li>Numeric offset applied to x values (default 0).</li>"
          "<li>Use to disambiguate overlapping series.</li>"
          "</ul></html>"
        ),
        "xLabel": (
          "<html><ul>"
          "<li>Custom x-axis label; defaults to <code>xValues</code>.</li>"
          "<li>Use units where helpful.</li>"
          "</ul></html>"
        ),
        "xScale": (
          "<html><ul>"
          "<li><code>lin</code> | <code>log</code> | <code>log10</code> | <code>order</code> (LinePlot only).</li>"
          "<li>Default is <code>lin</code>; <code>order</code> places points equidistantly.</li>"
          "</ul></html>"
        ),
        "yValues": (
          "<html><ul>"
          "<li>Observable ID to plot on the y-axis.</li>"
          "<li>Must match <code>measurement.observableId</code> for overlays.</li>"
          "</ul></html>"
        ),
        "yOffset": (
          "<html><ul>"
          "<li>Numeric offset applied to y values (default 0).</li>"
          "<li>Use for stacked/shifted visuals.</li>"
          "</ul></html>"
        ),
        "yLabel": (
          "<html><ul>"
          "<li>Custom y-axis label; defaults to <code>yValues</code>.</li>"
          "<li>Include units where applicable.</li>"
          "</ul></html>"
        ),
        "yScale": (
          "<html><ul>"
          "<li><code>lin</code> | <code>log</code> | <code>log10</code>.</li>"
          "<li>Default is <code>lin</code>.</li>"
          "</ul></html>"
        ),
        "legendEntry": (
          "<html><ul>"
          "<li>Legend text; defaults to <code>datasetId</code>.</li>"
          "<li>Use concise, descriptive names.</li>"
          "</ul></html>"
        ),
      },
    },
  },
}


def column_whats_this(table: str, column: str):
    tbl = WHATS_THIS.get("tables", {}).get(table, {})
    cols = tbl.get("columns", {})
    return cols.get(column) or cols.get("*")
