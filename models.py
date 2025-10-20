from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class UserProfile:
    id: str
    name: str
    role: str
    email: str
    phone: str
    city: str
    state: str
    country: str
    avatar_url: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            role=data.get('role'),
            email=data.get('email'),
            phone=data.get('phone'),
            city=data.get('city'),
            state=data.get('state'),
            country=data.get('country'),
            avatar_url=data.get('avatar_url'),
            created_at=datetime.fromisoformat(data.get('created_at')) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data.get('updated_at')) if data.get('updated_at') else None
        )

@dataclass
class PrivacySettings:
    user_id: str
    real_time_monitoring: bool = False
    data_retention: bool = False
    detailed_reporting: bool = False
    internal_communications: bool = False
    notifications: bool = False
    real_time_alerts: bool = False
    created_at: datetime = None
    updated_at: datetime = None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            user_id=data.get('user_id'),
            real_time_monitoring=data.get('real_time_monitoring', False),
            data_retention=data.get('data_retention', False),
            detailed_reporting=data.get('detailed_reporting', False),
            internal_communications=data.get('internal_communications', False),
            notifications=data.get('notifications', False),
            real_time_alerts=data.get('real_time_alerts', False),
            created_at=datetime.fromisoformat(data.get('created_at')) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data.get('updated_at')) if data.get('updated_at') else None
        )

@dataclass
class AdminAccess:
    id: str
    name: str
    role: str
    email: str
    avatar_url: Optional[str] = None
    permissions: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            role=data.get('role'),
            email=data.get('email'),
            avatar_url=data.get('avatar_url'),
            permissions=data.get('permissions', []),
            created_at=datetime.fromisoformat(data.get('created_at')) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data.get('updated_at')) if data.get('updated_at') else None
        )

@dataclass
class SubscriptionPlan:
    id: str
    name: str
    price: float
    billing_period: str  # 'monthly' or 'annually'
    features: List[str]
    is_custom: bool = False
    created_at: datetime = None
    updated_at: datetime = None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            price=float(data.get('price', 0)),
            billing_period=data.get('billing_period'),
            features=data.get('features', []),
            is_custom=data.get('is_custom', False),
            created_at=datetime.fromisoformat(data.get('created_at')) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data.get('updated_at')) if data.get('updated_at') else None
        )

@dataclass
class UserSubscription:
    user_id: str
    plan_id: str
    status: str  # 'active', 'cancelled', 'expired'
    start_date: datetime
    end_date: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            user_id=data.get('user_id'),
            plan_id=data.get('plan_id'),
            status=data.get('status'),
            start_date=datetime.fromisoformat(data.get('start_date')),
            end_date=datetime.fromisoformat(data.get('end_date')) if data.get('end_date') else None,
            created_at=datetime.fromisoformat(data.get('created_at')) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data.get('updated_at')) if data.get('updated_at') else None
        )
