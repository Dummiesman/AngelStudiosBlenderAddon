class TerSection:
    def __init__(self, bounds_min, bounds_max, edges, polygon):
        self.edges = edges
        self.bounds = (bounds_min, bounds_max)
        self.polygon = polygon
        self.group = []
        
