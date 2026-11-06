from ICERPython.BitPlaneCoding.Models.ContextModel import ContextModel

class ProbabilityEstimation:
    def __init__(self, context_model=None):
        self.context = ContextModel() if context_model is None else context_model

    def update_counts(self, context, bit):
        if context is not None:
            self.context.update_context(context, bit)

    def estimate_probability(self, context):
        if context is None:
            return 0.5
        counts = self.context.contexts[context]
        return counts["totalZeroBits"] / counts["totalBits"]

    def rescale_counts(self):
        for context, counts in self.context.contexts.items():
            if counts["totalBits"] >= 500:
                self.context.halve_context(context)
