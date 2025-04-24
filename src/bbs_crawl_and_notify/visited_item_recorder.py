class VisitedItemRecorder:

    def __init__(self, tags: list):
        """This function initializes the object.

        Args:
            tags (list): |tags| is optional. |tags| is shallow-copied using `copy()` call.
        """
        self.tags = tags.copy()
        self.visited_items = set()

    def is_visited(self, item: str):
        return item in self.visited_items

    def add_item(self, item: str):
        self.visited_items.add(item)

    def get_visited_items(self):
        return self.visited_items