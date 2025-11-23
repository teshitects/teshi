class TestCaseModel:
    """
    Test case model class, representing the attributes of a test case.
    
    Attributes:
        name (str): Name of the test case.
        number (str): Test case number.
        preconditions (str): Preconditions for the test.
        steps (str): Test steps.
        expected_results (str): Expected results.
        notes (str, optional): Additional notes.
        priority (str): Priority of the test case.
        domain (str): Domain or category.
        stage (str): Testing stage.
        feature (str): Feature module.
        uuid (str): Unique identifier.
        automate (bool): Whether the test is automated.
        tags (list[str], optional): List of tags.
        extras (dict, optional): Extra information.
    """
    def __init__(self, uuid, name, number, preconditions, steps, expected_results, notes, priority, domain, stage, feature
                 , automate, tags, extras):
        self.name = name
        self.number = number
        self.preconditions = preconditions
        self.steps = steps
        self.expected_results = expected_results
        self.notes = notes
        self.priority = priority
        self.domain = domain
        self.stage = stage
        self.feature = feature
        self.uuid = uuid
        self.automate = automate
        self.tags = tags
        self.extras = extras