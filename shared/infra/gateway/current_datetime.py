from datetime import datetime

from shared.domain.interface.gateway import ICurrentDatetimeGateway


class CurrentDatetimeGateway(ICurrentDatetimeGateway):
    def execute(self) -> datetime:
        return datetime.now()
