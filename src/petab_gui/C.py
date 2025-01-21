"""Constants for the PEtab edit GUI."""
COLUMNS = {
    "measurement": {
        "observableId": {"type": "STRING", "optional": False},
        "preequilibrationConditionId": {"type": "STRING", "optional": True},
        "simulationConditionId": {"type": "STRING", "optional": False},
        "time": {"type": "NUMERIC", "optional": False},
        "measurement": {"type": "NUMERIC", "optional": False},
        "observableParameters": {"type": "STRING", "optional": True},
        "noiseParameters": {"type": "STRING", "optional": True},
        "datasetId": {"type": "STRING", "optional": True},
        "replicateId": {"type": "STRING", "optional": True},
    },
    "observable": {
        "observableId": {"type": "STRING", "optional": False},
        "observableName": {"type": "STRING", "optional": True},
        "observableFormula": {"type": "STRING", "optional": False},
        "observableTransformation": {"type": "STRING", "optional": True},
        "noiseFormula": {"type": "STRING", "optional": False},
        "noiseDistribution": {"type": "STRING", "optional": True},
    },
    "parameter": {
        "parameterId": {"type": "STRING", "optional": False},
        "parameterName": {"type": "STRING", "optional": True},
        "parameterScale": {"type": "STRING", "optional": False},
        "lowerBound": {"type": "NUMERIC", "optional": False},
        "upperBound": {"type": "NUMERIC", "optional": False},
        "nominalValue": {"type": "NUMERIC", "optional": False},
        "estimate": {"type": "STRING", "optional": False},
        "initializationPriorType": {"type": "STRING", "optional": True},
        "initializationPriorParameters": {"type": "STRING", "optional": True},
        "objectivePriorType": {"type": "STRING", "optional": True},
        "objectivePriorParameters": {"type": "STRING", "optional": True},
    },
    "condition": {
        "conditionId": {"type": "STRING", "optional": False},
        "conditionName": {"type": "STRING", "optional": True},
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