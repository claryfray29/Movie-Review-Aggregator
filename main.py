from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
import crud, models, schemas
from datetime import timedelta
from database import SessionLocal, engine, get_db

from authentication import get_current_user, authenticate_user, create_access_token, Token, ACCESS_TOKEN_EXPIRE_MINUTES


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

#check if user exists for new user and create new acc
@app.post("/users/", response_model=schemas.Users)
def post_user(user:schemas.UsersCreate, db:Session=Depends(get_db)):
    db_user = crud.get_user(db, user_name=user.user_name)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    return crud.create_user(db=db, user=user)

#login
@app.post("/login", response_model=Token)
async def login_for_access_token(
    from_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, from_data.username, from_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.user_name})

    return{"access_token": access_token, "token_type": "bearer"}

# #login for old users
# @app.get("/users/{user_name}/", response_model=schemas.Users)
# def get_user(user_name: str, db:Session=Depends(get_db)):
#     db_user = crud.get_user(db, user_name=user_name)
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user

#search for a movie
@app.get("/movies/{movie_name}/", response_model=list[schemas.Movie])
async def get_movie(movie_name: str, db:Session=Depends(get_db), current_user = Depends(get_current_user)):
    return await crud.get_movie_list(db, movie_name = movie_name)
    # if not db_movie:
    #     raise HTTPException(status_code=404, detail="Movie not found")
    # return db_movie

# @app.get("/movies/search/{movie_name}/", response_model=list[schemas.Movie])
# async def search_movie(movie_name: str, db: Session = Depends(get_db)):
#     db_movies = await crud.get_movie(db, movie_name=movie_name)
#     if not db_movies:
#         raise HTTPException(status_code=404, detail="Movie not found")
#     return db_movies

@app.get("/movies/search/{movie_title}/", response_model=schemas.Movie)
async def get_movie_details(movie_title: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return await crud.get_movie_details(db, movie_title=movie_title)
    # if not db_movie:
    #     raise HTTPException(status_code=404, detail="Movie not found")
    # return db_movie

#add comment
@app.post("/movies/reviews/", response_model=schemas.Review)
def post_review(review: schemas.ReviewCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    
    return crud.create_review(db=db, review=review, user_name=current_user.user_name)

#update review
@app.put("/movies/reviews/{review_id}", response_model=schemas.Review)
def put_review(review_id: int, review_data: schemas.ReviewBase, db: Session=Depends(get_db), current_user: models.User=Depends(get_current_user)):
    db_review = crud.update_review(db=db, user_name=current_user.user_name, review_id=review_id, rating=review_data.rating, comment=review_data.comment)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    return db_review

#delete review
@app.delete("/movies/reviews/{review_id}")
def remove_review(review_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    success = crud.delete_review(db, current_user.user_name, review_id)
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"Detail": "Review deleted"}