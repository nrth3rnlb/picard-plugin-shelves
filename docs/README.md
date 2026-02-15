# Rule of thumb (for patch)

Patch where it is looked up, not where it "logically belongs."
For local imports in functions, you usually patch the original module (here shelves.processors.instance)
because there is no stable name in shelves.actions.

# Note for spec_set

If the spec class has side effects when instantiated (like picard.file.File):
Spec is always transferred as a class/type, not as a real object.

# Rule of thumb (so that it sticks)

spec_set=<class>: only if the class has its relevant attributes as properties/class attributes (or I really only
need the methods).
spec=<class>: if I need to set instance attributes that are only created at runtime (such as filename, metadata,
tracks, files).
