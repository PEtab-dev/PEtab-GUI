"""Constants for the PEtab edit GUI."""

import numpy as np
import petab.v1.C as PETAB_C

#: Application name
APP_NAME = "PEtab-GUI"
#: Base URL of the repository
REPO_URL = "https://github.com/PEtab-dev/PEtab-GUI"
#: Base URL of the documentation
DOCS_URL = "https://petab-gui.readthedocs.io/en/latest/"

COLUMNS = {
    "measurement": {
        PETAB_C.OBSERVABLE_ID: {"type": np.object_, "optional": False},
        PETAB_C.PREEQUILIBRATION_CONDITION_ID: {
            "type": np.object_,
            "optional": True,
        },
        PETAB_C.SIMULATION_CONDITION_ID: {
            "type": np.object_,
            "optional": False,
        },
        PETAB_C.TIME: {"type": np.float64, "optional": False},
        PETAB_C.MEASUREMENT: {"type": np.float64, "optional": False},
        PETAB_C.OBSERVABLE_PARAMETERS: {"type": np.object_, "optional": True},
        PETAB_C.NOISE_PARAMETERS: {"type": np.object_, "optional": True},
        PETAB_C.DATASET_ID: {"type": np.object_, "optional": True},
        PETAB_C.REPLICATE_ID: {"type": np.object_, "optional": True},
    },
    "simulation": {
        PETAB_C.OBSERVABLE_ID: {"type": np.object_, "optional": False},
        PETAB_C.PREEQUILIBRATION_CONDITION_ID: {
            "type": np.object_,
            "optional": True,
        },
        PETAB_C.SIMULATION_CONDITION_ID: {
            "type": np.object_,
            "optional": False,
        },
        PETAB_C.TIME: {"type": np.float64, "optional": False},
        PETAB_C.SIMULATION: {"type": np.float64, "optional": False},
        PETAB_C.OBSERVABLE_PARAMETERS: {"type": np.object_, "optional": True},
        PETAB_C.NOISE_PARAMETERS: {"type": np.object_, "optional": True},
        PETAB_C.DATASET_ID: {"type": np.object_, "optional": True},
        PETAB_C.REPLICATE_ID: {"type": np.object_, "optional": True},
    },
    "observable": {
        PETAB_C.OBSERVABLE_ID: {"type": np.object_, "optional": False},
        PETAB_C.OBSERVABLE_NAME: {"type": np.object_, "optional": True},
        PETAB_C.OBSERVABLE_FORMULA: {"type": np.object_, "optional": False},
        PETAB_C.OBSERVABLE_TRANSFORMATION: {
            "type": np.object_,
            "optional": True,
        },
        PETAB_C.NOISE_FORMULA: {"type": np.object_, "optional": False},
        PETAB_C.NOISE_DISTRIBUTION: {"type": np.object_, "optional": True},
    },
    "parameter": {
        PETAB_C.PARAMETER_ID: {"type": np.object_, "optional": False},
        PETAB_C.PARAMETER_NAME: {"type": np.object_, "optional": True},
        PETAB_C.PARAMETER_SCALE: {"type": np.object_, "optional": False},
        PETAB_C.LOWER_BOUND: {"type": np.float64, "optional": False},
        PETAB_C.UPPER_BOUND: {"type": np.float64, "optional": False},
        PETAB_C.NOMINAL_VALUE: {"type": np.float64, "optional": False},
        PETAB_C.ESTIMATE: {"type": np.object_, "optional": False},
        PETAB_C.INITIALIZATION_PRIOR_TYPE: {
            "type": np.object_,
            "optional": True,
        },
        PETAB_C.INITIALIZATION_PRIOR_PARAMETERS: {
            "type": np.object_,
            "optional": True,
        },
        PETAB_C.OBJECTIVE_PRIOR_TYPE: {"type": np.object_, "optional": True},
        PETAB_C.OBJECTIVE_PRIOR_PARAMETERS: {
            "type": np.object_,
            "optional": True,
        },
    },
    "condition": {
        PETAB_C.CONDITION_ID: {"type": np.object_, "optional": False},
        PETAB_C.CONDITION_NAME: {"type": np.object_, "optional": False},
    },
    "visualization": {
        PETAB_C.PLOT_ID: {"type": np.object_, "optional": False},
        PETAB_C.PLOT_NAME: {"type": np.object_, "optional": True},
        PETAB_C.PLOT_TYPE_SIMULATION: {
            "type": np.object_,
            "optional": True,
        },
        PETAB_C.PLOT_TYPE_DATA: {"type": np.object_, "optional": True},
        PETAB_C.DATASET_ID: {"type": np.object_, "optional": True},
        PETAB_C.X_VALUES: {"type": np.object_, "optional": True},
        PETAB_C.X_OFFSET: {"type": np.float64, "optional": True},
        PETAB_C.X_LABEL: {"type": np.object_, "optional": True},
        PETAB_C.X_SCALE: {"type": np.object_, "optional": True},
        PETAB_C.Y_VALUES: {"type": np.object_, "optional": True},
        PETAB_C.Y_OFFSET: {"type": np.float64, "optional": True},
        PETAB_C.Y_LABEL: {"type": np.object_, "optional": True},
        PETAB_C.Y_SCALE: {"type": np.object_, "optional": True},
        PETAB_C.LEGEND_ENTRY: {"type": np.object_, "optional": True},
    },
}

CONFIG = {
    "window_title": "My Application",
    "window_size": (800, 600),
    "table_titles": {
        "data": "Data",
        "parameters": "Parameters",
        "observables": "Observables",
        "conditions": "Conditions",
    },
    "summary_title": "Summary",
    "buttons": {
        "test_consistency": "Test Consistency",
        "proceed_optimization": "Proceed to Optimization",
    },
}

# String constants
ROW = "row"
COLUMN = "column"
INDEX = "index"

COPY_FROM = "copy from"
USE_DEFAULT = "use default"
NO_DEFAULT = "no default"
MIN_COLUMN = "use column min"
MAX_COLUMN = "use column max"
MODE = "use most frequent"
SBML_LOOK = "sbml value"
STRATEGIES_DEFAULT = [COPY_FROM, USE_DEFAULT, NO_DEFAULT]
STRATEGIES_DEFAULT_EXT = STRATEGIES_DEFAULT + [MODE]
STRATEGIES_DEFAULT_ALL = STRATEGIES_DEFAULT_EXT + [MIN_COLUMN, MAX_COLUMN]
STRATEGY_TOOLTIP = {
    COPY_FROM: "Copy from another column in the same row",
    USE_DEFAULT: "Use default value",
    NO_DEFAULT: "Do not set a value",
    MIN_COLUMN: "Use the minimum value of the column",
    MAX_COLUMN: "Use the maximum value of the column",
    MODE: "Use the most frequent value of the column",
    SBML_LOOK: "Use the value from the SBML model",
}
SOURCE_COLUMN = "source_column"
DEFAULT_VALUE = "default_value"

# Default Configurations of Default Values
ALLOWED_STRATEGIES_OBS = {
    PETAB_C.OBSERVABLE_ID: STRATEGIES_DEFAULT,
    PETAB_C.OBSERVABLE_NAME: STRATEGIES_DEFAULT,
    PETAB_C.OBSERVABLE_FORMULA: STRATEGIES_DEFAULT,
    PETAB_C.OBSERVABLE_TRANSFORMATION: [USE_DEFAULT, NO_DEFAULT, MODE],
    PETAB_C.NOISE_FORMULA: [COPY_FROM, USE_DEFAULT, NO_DEFAULT, MODE],
    PETAB_C.NOISE_DISTRIBUTION: [USE_DEFAULT, NO_DEFAULT, MODE],
}
ALLOWED_STRATEGIES_PAR = {
    PETAB_C.PARAMETER_ID: STRATEGIES_DEFAULT,
    PETAB_C.PARAMETER_NAME: STRATEGIES_DEFAULT,
    PETAB_C.PARAMETER_SCALE: [USE_DEFAULT, NO_DEFAULT, MODE],
    PETAB_C.LOWER_BOUND: [
        MIN_COLUMN,
        MAX_COLUMN,
        USE_DEFAULT,
        NO_DEFAULT,
        MODE,
    ],
    PETAB_C.UPPER_BOUND: [
        MAX_COLUMN,
        MAX_COLUMN,
        USE_DEFAULT,
        NO_DEFAULT,
        MODE,
    ],
    PETAB_C.NOMINAL_VALUE: [USE_DEFAULT, NO_DEFAULT, SBML_LOOK],
    PETAB_C.ESTIMATE: [USE_DEFAULT, NO_DEFAULT, MODE],
}
ALLOWED_STRATEGIES_COND = {
    PETAB_C.CONDITION_ID: STRATEGIES_DEFAULT,
    PETAB_C.CONDITION_NAME: STRATEGIES_DEFAULT,
}
ALLOWED_STRATEGIES_MEAS = {
    PETAB_C.OBSERVABLE_ID: STRATEGIES_DEFAULT,
    PETAB_C.PREEQUILIBRATION_CONDITION_ID: STRATEGIES_DEFAULT_EXT,
    PETAB_C.SIMULATION_CONDITION_ID: STRATEGIES_DEFAULT_EXT,
    PETAB_C.TIME: [NO_DEFAULT, USE_DEFAULT, MODE],
    PETAB_C.MEASUREMENT: [NO_DEFAULT, USE_DEFAULT, MODE],
    PETAB_C.OBSERVABLE_PARAMETERS: STRATEGIES_DEFAULT_EXT,
    PETAB_C.NOISE_PARAMETERS: STRATEGIES_DEFAULT_EXT,
    PETAB_C.DATASET_ID: [COPY_FROM, USE_DEFAULT, NO_DEFAULT, MODE],
    PETAB_C.REPLICATE_ID: [COPY_FROM, USE_DEFAULT, NO_DEFAULT, MODE],
}
ALLOWED_STRATEGIES = {
    "observable": ALLOWED_STRATEGIES_OBS,
    "parameter": ALLOWED_STRATEGIES_PAR,
    "condition": ALLOWED_STRATEGIES_COND,
    "measurement": ALLOWED_STRATEGIES_MEAS,
}
DEFAULT_OBS_CONFIG = {
    PETAB_C.OBSERVABLE_ID: {
        "strategy": COPY_FROM,
        SOURCE_COLUMN: PETAB_C.OBSERVABLE_FORMULA,
        DEFAULT_VALUE: "new_observable",
    },
    PETAB_C.OBSERVABLE_NAME: {
        "strategy": COPY_FROM,
        SOURCE_COLUMN: PETAB_C.OBSERVABLE_ID,
    },
    PETAB_C.NOISE_FORMULA: {"strategy": USE_DEFAULT, DEFAULT_VALUE: 1},
    PETAB_C.OBSERVABLE_TRANSFORMATION: {
        "strategy": USE_DEFAULT,
        DEFAULT_VALUE: PETAB_C.LIN,
    },
    PETAB_C.NOISE_DISTRIBUTION: {
        "strategy": USE_DEFAULT,
        DEFAULT_VALUE: PETAB_C.NORMAL,
    },
}
DEFAULT_PAR_CONFIG = {
    PETAB_C.PARAMETER_NAME: {
        "strategy": COPY_FROM,
        SOURCE_COLUMN: PETAB_C.PARAMETER_ID,
        DEFAULT_VALUE: "new_parameter",
    },
    PETAB_C.PARAMETER_SCALE: {
        "strategy": USE_DEFAULT,
        DEFAULT_VALUE: PETAB_C.LOG10,
    },
    PETAB_C.LOWER_BOUND: {"strategy": MIN_COLUMN},
    PETAB_C.UPPER_BOUND: {"strategy": MAX_COLUMN},
    PETAB_C.ESTIMATE: {"strategy": USE_DEFAULT, DEFAULT_VALUE: 1},
    PETAB_C.NOMINAL_VALUE: {"strategy": SBML_LOOK},
}
DEFAULT_COND_CONFIG = {
    PETAB_C.CONDITION_ID: {
        "strategy": USE_DEFAULT,
        DEFAULT_VALUE: "new_condition",
    },
    PETAB_C.CONDITION_NAME: {
        "strategy": COPY_FROM,
        SOURCE_COLUMN: PETAB_C.CONDITION_ID,
    },
}
DEFAULT_MEAS_CONFIG = {}
DEFAULT_CONFIGS = {
    "observable": DEFAULT_OBS_CONFIG,
    "parameter": DEFAULT_PAR_CONFIG,
    "condition": DEFAULT_COND_CONFIG,
    "measurement": DEFAULT_MEAS_CONFIG,
}

COMMON_ERRORS = {
    r"Error parsing '': Syntax error at \d+:\d+: mismatched input '<EOF>' "
    r"expecting \{[^}]+\}": "Invalid empty cell!"
}

DEFAULT_ANTIMONY_TEXT = """model *New_File

  // Compartments and Species:

  // Assignment Rules:

  // Reactions:

  // Species initializations:

  // Compartment initializations:

  // Variable initializations:

  // Other declarations:

  // Unit definitions:

  // Display Names:

  // Notes:


end
"""
