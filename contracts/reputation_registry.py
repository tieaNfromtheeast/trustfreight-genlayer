# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import genlayer as gl
from genlayer.types import *

class Contract(gl.Contract):
    # Mapping of address (as string) to score (u64)
    scores: gl.storage.TreeMap[str, u256]
    
    def __init__(self):
        # Base score is 100. Higher is better.
        pass

    @gl.public.view
    def get_score(self, entity: str) -> u256:
        return self.scores.get(entity, u256(100))

    @gl.public.write
    def update_score(self, entity: str, fault_percent: u256) -> None:
        current_score = self.get_score(entity)
        # If fault > 50, reduce score. If < 50, increase score.
        if fault_percent > u256(50):
            penalty = fault_percent - u256(50)
            if current_score > penalty:
                self.scores[entity] = current_score - penalty
            else:
                self.scores[entity] = u256(0)
        else:
            reward = u256(50) - fault_percent
            self.scores[entity] = current_score + reward
