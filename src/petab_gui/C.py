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