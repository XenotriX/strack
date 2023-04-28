from datetime import datetime
from typing import Optional
from .utils import format_duration


class Session:
    def __init__(self,
                 start: datetime,
                 end: Optional[datetime] = None,
                 comment: Optional[str] = None):
        self.start: datetime = start
        self.end: Optional[datetime] = end
        self.comment: Optional[str] = comment

    @staticmethod
    def from_obj(obj):
        try:
            start = datetime.fromisoformat(obj['start'])
            end = datetime.fromisoformat(obj['end'])
            comment = obj.get('comment', None)
            return Session(start=start, end=end, comment=comment)
        except ArithmeticError:
            raise Exception('Could not parse Session')

    def duration(self) -> float:
        return ((self.end or datetime.now()) - self.start).total_seconds()

    def duration_str(self) -> str:
        seconds = self.duration()
        return format_duration(seconds)

    def __repr__(self):
        return self.__dict__.__str__()

    def __serialize__(self):
        obj = {
            'start': str(self.start),
            'end': str(self.end)
        }
        if self.comment is not None:
            obj['comment'] = self.comment

        return obj
