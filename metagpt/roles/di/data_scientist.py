from metagpt.roles.di.data_interpreter import DataInterpreter

class DataScientist(DataInterpreter):
    def __init__(self, **kwargs):
        super().__init__(
            name="DataScientist",
            desc="A role focused on data preprocessing, feature engineering, and data cleaning.",
            **kwargs
        ) 