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

# Default Configurations of Default Values
DEFAULT_OBS_CONFIG = {
    "observableId": {
        "strategy": "copy_column", "source_column": "observableFormula",
        "prefix": "obs_", "default_value": ""
    },
    "observableName": {
        "strategy": "copy_column", "source_column": "observableId",
        "default_value": ""
    },
    "noiseFormula": {
        "strategy": "default_value", "default_value": 1
    },
    "observableTransformation": {
        "strategy": "default_value",
        "default_value": "lin"
    },
    "noiseDistribution": {
        "strategy": "default_value",
        "default_value": "normal"
    }
}
DEFAULT_PAR_CONFIG = {
    "parameterName": {
        "strategy": "copy_column", "source_column": "parameterId", "default_value": ""
    },
    "parameterScale": {
        "strategy": "default_value", "default_value": "log10"
    },
    "lowerBound": {
        "strategy": "min_column", "min_cap": 1e-8, "default_value": 1e-8
    },
    "upperBound": {
        "strategy": "max_column", "max_cap": 1e8, "default_value": 1e8
    },
    "estimate": {
        "strategy": "default_value", "default_value": 1
    },
}
DEFAULT_COND_CONFIG = {
    "conditionName": {
        "strategy": "copy_column", "source_column": "conditionId",
        "default_value": ""
    }
}
DEFAULT_MEAS_CONFIG = {}
DEFAULT_CONFIGS = {
    "observable": DEFAULT_OBS_CONFIG,
    "parameter": DEFAULT_PAR_CONFIG,
    "condition": DEFAULT_COND_CONFIG,
    "measurement": DEFAULT_MEAS_CONFIG
}
