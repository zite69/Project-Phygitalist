import warnings

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
