class Probe2Strategy:
    def execute(self, data):
        result = self.process_data(data)
        return result  # Fixed undefined name 'reuslt' to 'result'

    def process_data(self, data):
        # Some processing logic
        return data