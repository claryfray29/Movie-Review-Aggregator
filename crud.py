from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, text
from fastapi import HTTPException
import hashlib
import os
from datetime import datetime
import httpx
import models, schemas

#to login
def get_user(db: Session, user_name: str):
    return db.query(models.User).filter(models.User.user_name == user_name).first()

#to registeer new user
def create_user(db: Session, user:schemas.UsersCreate):
    db_user = models.User(user_name = user.user_name, user_login = hashlib.sha256(user.user_login.encode()).hexdigest())

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

#to search for a particular movie
async def get_movie(db: Session, movie_name: str):
    if not movie_name:
        raise HTTPException(status_code=400, detail="Movie title required.")
    
    movie_name=movie_name.title()

    #SET @name = '{movie_name}'
    query = text("SELECT * FROM movie WHERE movie_name LIKE :name")
    result = db.execute(query,{"name" : f"%{movie_name}%"}).fetchall()
    
    OMDB_API_KEY = os.getenv("OMDB_API_KEY")

    if not OMDB_API_KEY:
        raise HTTPException(status_code=500, detail="api key missing")

    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={movie_name}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)

            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Faited to fetch")

            data = response.json()

        if data.get("Response") == "True" and "Search" in data:
            omdb_movie = data.get("Search", [])
            saved_movies = []

            for item in omdb_movie:
                existing_stmt = select(models.Movie).where(models.Movie.movie_name == item.get("Title"))
                existing = db.execute(existing_stmt).scalars().first()
                if existing:
                    saved_movies.append(existing)
                    continue

                db_movie = models.Movie(
                    movie_name=item.get("Title"),
                    movie_genre="idk",
                    movie_director="Unknown",
                    other_info=item
                )

                db.add(db_movie)
                saved_movies.append(db_movie)

            db.commit()

            for movie in saved_movies:
                db.refresh(movie)

            return saved_movies

        else:
            raise HTTPException(status_code=404, detail="Movie not found")

    except httpx.RequestError:
        raise HTTPException(status_code=500, detail="Failed to fetch movie details")
            

#to add a review to some movie
def create_review(db: Session, review:schemas.ReviewCreate, user_name: str):
    db_movie = db.query(models.Movie).filter(models.Movie.movie_name == review.movie_name).first()

    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found") #WITHOUT EXTERNAL API

    all_rating = [i.rating for i in db_movie.reviews] + [review.rating]
    db_movie.avg_rating = sum(all_rating)/len(all_rating)

    db_review = models.Review(
        user_name=user_name,
        movie_id=db_movie.movie_id,
        rating=review.rating,
        comment=review.comment
    )

    db.add(db_review)

    

    db.commit()
    db.refresh(db_review)
    return db_review

def update_review(db: Session, user_name: str, review:schemas.ReviewCreate):
    db_movie = db.query(models.Movie).filter(models.Movie.movie_name == review.movie_name).first()

    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    db_review = db.query(models.Review).filter(models.Review.movie_id == db_movie.movie_id, models.Review.user_name == user_name).first()

    if db_review:
        db_review.rating = review.rating
        db_review.comment = review.comment
        db.commit()
        db.refresh(db_review)
    return db_review

def delete_review(db:Session, user_name: str, review:schemas.ReviewCreate):
    db_movie = db.query(models.Movie).filter(models.Movie.movie_name == review.movie_name).first()

    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    db_review = db.query(models.Review).filter(models.Review.movie_id == db_movie.movie_id, models.Review.user_name == user_name).first()

    if db_review:
        db.delete(db_review)
        db.commit()
        return True
    return False

# def get_movie_with_rating(db: Session, movie_name: str):
#     # Fetch movie and its reviews
#     stmt = select(models.Movie).options(joinedload(models.Movie.reviews)).where(models.Movie.movie_name == movie_name)
#     result = db.execute(stmt).scalars().first()
    
#     if result:
#         # Calculate Average Rating (Requirement: Data Aggregation)
#         ratings = [r.rating for r in result.reviews]
#         result.average_rating = sum(ratings) / len(ratings) if ratings else 0.0
#     return result