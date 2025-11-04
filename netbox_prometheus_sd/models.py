class Node(MPTTModel):
    ...
    class Meta:
        indexes = [
            models.Index(fields=["tree_id", "lft"]),
            # Optional if you filter on rght too:
            models.Index(fields=["tree_id", "rght"]),
        ]
