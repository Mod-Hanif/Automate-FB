class FBException(Exception):
    pass


class ShareLimitException(FBException):
    pass


class CommentLimitException(FBException):
    pass
