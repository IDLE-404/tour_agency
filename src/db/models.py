from dataclasses import dataclass


@dataclass(slots=True)
class User:
    id: int
    full_name: str
    username: str
    role: str


@dataclass(slots=True)
class Client:
    id: int
    full_name: str
    phone: str
    email: str | None
    document: str
    birth_date: str | None


@dataclass(slots=True)
class Tour:
    id: int
    name: str
    country: str
    city: str
    date_from: str
    date_to: str
    price: float
    seats: int
    description: str | None


@dataclass(slots=True)
class Booking:
    id: int
    client_id: int
    tour_id: int
    booking_date: str
    status: str
    amount: float
