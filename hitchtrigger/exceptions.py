class HitchTriggerException(Exception):
    pass


class DependentModelNotFound(HitchTriggerException):
    pass


class VarMustBePickleable(HitchTriggerException):
    pass
