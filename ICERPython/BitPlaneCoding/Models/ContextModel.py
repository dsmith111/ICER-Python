class ContextModel:
    def __init__(self):
        self.contexts: dict[int,dict] = {}
        # Add 0-16 contexts.
        for i in range(17):
            self.contexts[i] = {"totalBits": 4, "totalZeroBits": 2}
            
    def halve_context(self, context: int):
        total_bits = self.contexts[context]["totalBits"]
        zero_bits = self.contexts[context]["totalZeroBits"]
        self.contexts[context]["totalBits"] = total_bits // 2
        self.contexts[context]["totalZeroBits"] = (zero_bits + int(2 * zero_bits < total_bits)) // 2
        
    def update_context(self, context: int, bit: int):
        if bit not in [0, 1]:
            raise ValueError("A bit must be 0 or 1")
        self.contexts[context]["totalBits"] += 1
        self.contexts[context]["totalZeroBits"] += int(bit == 0)
        if self.contexts[context]["totalBits"] >= 500:
            self.halve_context(context)