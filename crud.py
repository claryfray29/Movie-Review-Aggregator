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
async def get_movie_list(db: Session, movie_name: str):
    if not movie_name:
        raise HTTPException(status_code=400, detail="Movie title required.")
    
    # movie_name=movie_name.title()

    # #SET @name = '{movie_name}'
    # query = text("SELECT * FROM movie WHERE movie_name LIKE :name")
    # result = db.execute(query,{"name" : f"%{movie_name}%"}).mappings().all()
    
    # if result:
    #     return result

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
            print(data)

        movies_list = []
        if data.get("Response") == "True" and "Search" in data:
            omdb_movie = data.get("Search", [])
            print(omdb_movie)
            # movies_list = []

            for item in omdb_movie:
                print(item)
                # existing_stmt = select(models.Movie).where(models.Movie.movie_name == item.get("Title"))
                # existing = db.execute(existing_stmt).scalars().first()
                # if existing:
                #     movies_list.append(existing)
                #     continue

                raw_year = item.get("Year")
                clean_year = None
                if raw_year:
                    try:
                        # Slice the first 4 characters to safely extract the start year (handles "1992–1995" -> 1992)
                        clean_year = int(str(raw_year)[:4])
                    except ValueError:
                        clean_year = None

                list_movie = {
                    "movie_name": item.get("Title"),
                    # "movie_genre": "idk",
                    "movie_year": clean_year,
                    "movie_director": "Unknown",
                    "other_info": item
                }
                movies_list.append(list_movie)

            #     db.add(db_movie)
            #     movies_list.append(db_movie)

            # db.commit()

            # for movie in movies_list:
            #     db.refresh(movie)

        return movies_list
    #     else:
    #         raise HTTPException(status_code=404, detail="Movie not found")

    except httpx.RequestError:
        raise HTTPException(status_code=500, detail="Failed to fetch movie details")
            

#to get more details
async def get_movie_details(db: Session, movie_title: str):
    if not movie_title:
        raise HTTPException(status_code=400, detail="Movie title is required.")

    db_movie = db.query(models.Movie).filter(models.Movie.movie_name == movie_title).first()
    if db_movie:
        return db_movie
    #     raise HTTPException(status_code=404, detail="Movie not found in local db")

    OMDB_API_KEY = os.getenv("OMDB_API_KEY")
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")
    if not OMDB_API_KEY or not TMDB_API_KEY:
        raise HTTPException(status_code=500, detail="api keys missing")

    # imdb_id = db_movie.other_info.get("imdbID") if db_movie.other_info else None
    # if imdb_id:
    #     url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}"
    # else:

    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={movie_title.strip()}&plot=full"
    tmdb_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_title.strip()}"

    try:
        async with httpx.AsyncClient() as client:
            omdb_response = await client.get(url)

            if omdb_response.status_code == 200:
                omdb_data = omdb_response.json()

            if omdb_data.get("Response") == "True":
                raw_year = omdb_data.get("Year")
                clean_year = int(str(raw_year)[:4]) if raw_year and raw_year != "N/A" else None

                release_date = omdb_data.get("Released")
                if release_date and release_date != "N/A":
                    try:
                        release_date = datetime.strptime(release_date, "%d %b %Y").date()
                    except ValueError:
                        release_date = None

                # db_movie.movie_date = release_date
                # db_movie.movie_genre = omdb_data.get("Genre", "Unknown") if omdb_data.get("Genre") != "N/A" else "Unknown"
                # db_movie.movie_director = omdb_data.get("Director", "Unknown") if omdb_data.get("Director") != "N/A" else "Unknown"
                # db_movie.imdb_id = omdb_data.get("imdbID", db_movie.imdb_id)
                # db_movie.other_info = omdb_data
                # db_movie.movie_plot = omdb_data.get("Plot", "Unknown") if omdb_data.get("Plot") != "N/A" else "Unknown"
                
                db_movie = models.Movie(
                    movie_name=omdb_data.get("Title"),
                    imdb_id=omdb_data.get("imdbID"),
                    movie_year=clean_year,
                    movie_date=release_date,
                    movie_genre=omdb_data.get("Genre", "Unknown") if omdb_data.get("Genre") != "N/A" else "Unknown",
                    movie_director=omdb_data.get("Director", "Unknown") if omdb_data.get("Director") != "N/A" else "Unknown",
                    movie_plot=omdb_data.get("Plot", "Unknown") if omdb_data.get("Plot") != "N/A" else "Unknown",
                    other_info=omdb_data
                )

                db.add(db_movie)
                db.commit()
                db.refresh(db_movie)
                return db_movie
        # else:
        #     raise HTTPException(status_code=404, detail="Movie details not found")

    except httpx.RequestError:
        raise HTTPException(status_code=500, detail="Failed to fetch movie details")

    try:
        async with httpx.AsyncClient() as client:
            tmdb_response = await client.get(tmdb_url)

            if tmdb_response.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to fetch from TMDB")

            tmdb_data = tmdb_response.json()    

            if tmdb_data.get("results"):
                tmdb_movie = tmdb_data["results"][0]
                print("tmdb saved")

                release_date = None
                raw_date=tmdb_movie.get("release_date")
                clean_year = None
                if raw_date:
                    try:
                        release_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
                        clean_year = release_date.year
                    except ValueError:
                        release_date = None
                
                poster_path = tmdb_movie.get("poster_path")
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

                db_movie = models.Movie(
                    movie_name=tmdb_movie.get("title"),
                    movie_year=clean_year,
                    movie_date=release_date,
                    movie_genre="Unknown",
                    movie_director="Unknown",
                    movie_plot="Unknown",
                    poster_url=poster_url,
                    other_info=tmdb_movie
                )
                db.add(db_movie)
                db.commit()
                db.refresh(db_movie)
                return db_movie
            else:
                raise HTTPException(status_code=404, detail="Movie details not found in TMDB") 
    except httpx.RequestError:
        raise HTTPException(status_code=500, detail="Failed to fetch from TMDB")

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