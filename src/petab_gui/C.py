"""Constants for the PEtab edit GUI."""
import numpy as np

COLUMNS = {
    "measurement": {
        "observableId": {"type": np.object_, "optional": False},
        "preequilibrationConditionId": {"type": np.object_, "optional": True},
        "simulationConditionId": {"type": np.object_, "optional": False},
        "time": {"type": np.float64, "optional": False},
        "measurement": {"type": np.float64, "optional": False},
        "observableParameters": {"type": np.object_, "optional": True},
        "noiseParameters": {"type": np.object_, "optional": True},
        "datasetId": {"type": np.object_, "optional": True},
        "replicateId": {"type": np.object_, "optional": True},
    },
    "observable": {
        "observableId": {"type": np.object_, "optional": False},
        "observableName": {"type": np.object_, "optional": True},
        "observableFormula": {"type": np.object_, "optional": False},
        "observableTransformation": {"type": np.object_, "optional": True},
        "noiseFormula": {"type": np.object_, "optional": False},
        "noiseDistribution": {"type": np.object_, "optional": True},
    },
    "parameter": {
        "parameterId": {"type": np.object_, "optional": False},
        "parameterName": {"type": np.object_, "optional": True},
        "parameterScale": {"type": np.object_, "optional": False},
        "lowerBound": {"type": np.float64, "optional": False},
        "upperBound": {"type": np.float64, "optional": False},
        "nominalValue": {"type": np.float64, "optional": False},
        "estimate": {"type": np.object_, "optional": False},
        "initializationPriorType": {"type": np.object_, "optional": True},
        "initializationPriorParameters": {"type": np.object_, "optional": True},
        "objectivePriorType": {"type": np.object_, "optional": True},
        "objectivePriorParameters": {"type": np.object_, "optional": True},
    },
    "condition": {
        "conditionId": {"type": np.object_, "optional": False},
        "conditionName": {"type": np.object_, "optional": False},
    }
    }

CONFIG = {
    'window_title': 'My Application',
    'window_size': (800, 600),
    'table_titles': {
        'data': 'Data',
        'parameters': 'Parameters',
        'observables': 'Observables',
        'conditions': 'Conditions'
    },
    'summary_title': 'Summary',
    'buttons': {
        'test_consistency': 'Test Consistency',
        'proceed_optimization': 'Proceed to Optimization'
    }
}

# String constants
ROW = 'row'
COLUMN = 'column'
INDEX = 'index'

COPY_FROM = "copy from"
USE_DEFAULT = "use default"
NO_DEFAULT = "no default"
MIN_COLUMN = "use column min"
MAX_COLUMN = "use column max"
MODE = "use most frequent"
STRATEGIES_DEFAULT = [COPY_FROM, USE_DEFAULT, NO_DEFAULT, MIN_COLUMN,
                      MAX_COLUMN, MODE]
STRATEGY_TOOLTIP = {
    COPY_FROM: "Copy from another column in the same row",
    USE_DEFAULT: "Use default value",
    NO_DEFAULT: "Do not set a value",
    MIN_COLUMN: "Use the minimum value of the column",
    MAX_COLUMN: "Use the maximum value of the column",
}
SOURCE_COLUMN = "source_column"
DEFAULT_VALUE = "default_value"

# Default Configurations of Default Values
DEFAULT_OBS_CONFIG = {
    "observableId": {
        "strategy": COPY_FROM, SOURCE_COLUMN: "observableFormula",
        DEFAULT_VALUE: "new_observable"
    },
    "observableName": {
        "strategy": COPY_FROM, SOURCE_COLUMN: "observableId"
    },
    "noiseFormula": {
        "strategy": USE_DEFAULT, DEFAULT_VALUE: 1
    },
    "observableTransformation": {
        "strategy": USE_DEFAULT,
        DEFAULT_VALUE: "lin"
    },
    "noiseDistribution": {
        "strategy": USE_DEFAULT,
        DEFAULT_VALUE: "normal"
    }
}
DEFAULT_PAR_CONFIG = {
    "parameterName": {
        "strategy": COPY_FROM, SOURCE_COLUMN: "parameterId",
        DEFAULT_VALUE: "new_parameter"
    },
    "parameterScale": {
        "strategy": USE_DEFAULT, DEFAULT_VALUE: "log10"
    },
    "lowerBound": {
        "strategy": MIN_COLUMN
    },
    "upperBound": {
        "strategy": MAX_COLUMN
    },
    "estimate": {
        "strategy": USE_DEFAULT, DEFAULT_VALUE: 1
    },
}
DEFAULT_COND_CONFIG = {
    "conditionId": {
        "strategy": USE_DEFAULT, DEFAULT_VALUE: "new_condition"
    },
    "conditionName": {
        "strategy": COPY_FROM, SOURCE_COLUMN: "conditionId"
    }
}
DEFAULT_MEAS_CONFIG = {}
DEFAULT_CONFIGS = {
    "observable": DEFAULT_OBS_CONFIG,
    "parameter": DEFAULT_PAR_CONFIG,
    "condition": DEFAULT_COND_CONFIG,
    "measurement": DEFAULT_MEAS_CONFIG
}
