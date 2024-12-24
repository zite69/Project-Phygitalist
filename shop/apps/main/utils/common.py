import warnings

def get_deep_obj(obj, property_path):
    """
        Given an object, gets a property nested deep within it.
        For example if you have a user with a profile and the profile has an address. 
        You can use:
        >>> address = get_deep_obj(user, 'profile.address')
    """
    head, *tail = property_path.split(".")
    newobj = getattr(obj, head)
    if not newobj:
        return obj
    else:
        return get_deep_obj(newobj, ".".join(tail))

def dump(obj, logger):
  for name in dir(obj):
    e = False
    with warnings.catch_warnings():
      warnings.simplefilter("ignore")
      try:
        v = getattr(obj, name)
      except:
        e = True
      warnings.simplefilter("default")
    if not e:
      logger.debug("obj.%s = %r" % (name, v))
    else:
      logger.debug("<inaccessible property obj.%s>" % name)
