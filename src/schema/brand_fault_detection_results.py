from sqlalchemy import INT, NVARCHAR, Column, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BrandFaultDetectionResults(Base):
    # __tablename__ = 'BrandFaultDetection_Results'
    __tablename__ = "ip_kamera_deneme"

    ID = Column(INT, nullable=False, primary_key=True)
    DeviceID = Column(INT, nullable=False)
    Date = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    BrandName = Column(NVARCHAR(None), nullable=False)
    State = Column(INT, nullable=False)

    def __repr__(self):
        return (
            f"BrandFaultDetection_Results(ID={self.ID!r}, "
            f"DeviceID={self.DeviceID!r}, "
            f"Date={self.Date!r}, "
            f"BrandName={self.BrandName!r}, "
            f"State={self.State!r})"
        )
