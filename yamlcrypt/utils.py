def namespace_to_dataclass(namespace, dataclass_type):
    """Helper function to translate any namespace into a dataclass with args founrd in the namespace"""
    relevant_args = {
        key: value
        for key, value in vars(namespace).items()
        if key in dataclass_type.__annotations__
    }
    return dataclass_type(**relevant_args)
