CREATE DATABASE movieAggregator;

USE movieAggregator;

CREATE TABLE users(
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(255) UNIQUE,
    user_login VARCHAR(255)
);

CREATE TABLE movie(
    movie_id INT AUTO_INCREMENT PRIMARY KEY,
    imdb_id VARCHAR(50) UNIQUE NULL,
    movie_name VARCHAR(255),
    movie_year INT,
    movie_genre VARCHAR(255),
    movie_director VARCHAR(255),
    movie_plot VARCHAR(1000) NULL,
    avg_rating FLOAT DEFAULT 0,
    other_info JSON
);

CREATE TABLE movieReview(
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(255),
    movie_id INT,
    rating INT CHECK (RATING <= 5),
    comment TEXT,

    FOREIGN KEY (user_name) REFERENCES users(user_name),
    FOREIGN KEY (movie_id) REFERENCES movie(movie_id)
);
