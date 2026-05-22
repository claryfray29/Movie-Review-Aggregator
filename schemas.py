from pydantic import BaseModel
from datetime import date

class UsersBase(BaseModel):
    user_name: str
    user_login: str


class UsersCreate(UsersBase):
    pass

class Users(BaseModel):
    user_id: int
    user_name: str
    user_login: str

    class Config:
        from_attributes = True



class ReviewBase(BaseModel):
    rating: int
    comment: str


class ReviewCreate(ReviewBase):
    movie_name: str

class Review(ReviewBase):
    user_name: str

    class Config:
        from_attributes = True



class MovieBase(BaseModel):
    movie_name: str
    movie_year: int | None = None
    movie_genre: str
    movie_director: str
    movie_plot: str | None = None


class MovieCreate(MovieBase):
    pass

class Movie(MovieBase):
    movie_id: int
    movie_year: int | None = None
    movie_date: date | None = None
    avg_rating: float
    reviews: list[Review] = []

    class Config:
        from_attributes = True

