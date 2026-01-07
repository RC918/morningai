# BEFORE
def get_product(db, id):
    return db.get(id)

# AFTER
def get_product(db: Database, id: int) -> Optional[Product]:
    """
    Fetch a product by its ID from the database.

    :param db: The database connection
    :param id: The ID of the product
    :return: The Product object or None if not found
    """
    product = db.get(id)
    return product