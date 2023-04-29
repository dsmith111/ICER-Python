class ContextModel:
    def __init__(self):
        self.contexts: dict[int,dict] = {}
        # Add 0-16 contexts.
        for i in range(17):
            self.contexts[i] = {"totalBits": 0, "totalZeroBits": 0}
            
    def halve_context(self, context: int):
        self.contexts[context]["totalBits"] /= 2
        self.contexts[context]["totalZeroBits"] /= 2
        
    def update_context(self, context: int, bit: int):
        self.contexts[context]["totalBits"] += 1
        self.contexts[context]["totalZeroBits"] += bit
        if self.contexts[context]["totalBits"] >= 500:
            self.halve_context(context)