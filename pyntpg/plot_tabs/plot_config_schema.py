import cerberus


config_schema = {
    "y-axis": {},
    "z-axis": {},

}


def validate_config(schema, config):
    """
    Ensure that the config dict contains at minimum, some set of expected key/value pairs.
    Configure validation with self.base_config_schema. See [1] for schema documentation.
    [1] http://docs.python-cerberus.org/en/stable/schemas.html

    :type schema: dict
    :param schema: Cerberus schema specifying validation.
    :type config: dict
    :param config: Configuration to be validated against schema.
    :rtype: dict
    :return: Validated configuration, possibly with type coerced.
    """
    if schema is None:
        return config

    v = cerberus.Validator(schema, purge_unknown=False)
    if v.validate(config):
        return v.document
    else:
        raise ValueError(v.errors)