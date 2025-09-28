# Mock vector store for long-term memory
memory = {}

def recall(key): return memory.get(key, {})
def save(key, val): memory[key] = val
