from sqlalchemy import Integer, String, Float, Column, ForeignKey, Date, JSON
from sqlalchemy.orm import relationship

from database import Base

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(255), unique=True)
    user_login = Column(String(255))

    reviews = relationship("Review", back_populates="user")

class Movie(Base):
    __tablename__ = 'movie'
    
    movie_id = Column(Integer, primary_key=True, autoincrement=True)
    imdb_id = Column(String(50), unique=True, nullable=True)
    movie_name = Column(String(255))
    movie_year = Column(Integer, nullable = True)
    movie_date = Column(Date, nullable=True)
    movie_genre = Column(String(255), nullable = True)
    movie_director = Column(String(255))
    movie_plot = Column(String(1000), nullable=True)
    avg_rating = Column(Float, default=0)
    other_info = Column(JSON, nullable=True)

    reviews = relationship("Review", back_populates="movie")
    

class Review(Base):
    __tablename__ = 'movieReview'
    
    review_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(255), ForeignKey('users.user_name'))
    movie_id = Column(Integer, ForeignKey('movie.movie_id'))
    rating = Column(Integer)
    comment = Column(String(300))

    user = relationship("User", back_populates="reviews")
    movie = relationship("Movie", back_populates="reviews")
