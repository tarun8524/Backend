from fastapi import FastAPI, APIRouter, HTTPException
from datetime import datetime, time
from pydantic import BaseModel
from typing import List, Dict
import spacy #type: ignore
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer #type: ignore
from pymongo import MongoClient #type: ignore
from urllib.parse import quote_plus
from API import api_db_handler

# Load spaCy and VADER
nlp = spacy.load("en_core_web_sm")
vader = SentimentIntensityAnalyzer()


feedback_collection = api_db_handler.db["feedback"]

class Feedback(BaseModel):
    name: str
    rating: int
    feedback: str
    camera_name: str
    time_elapsed: str
    sentiment_label: str

class RatingSentimentCounts(BaseModel):
    ratings: Dict[str, int]
    sentiments: Dict[str, int]

class FeedbackAPI:
    def __init__(self):
        self.router = APIRouter()
        self.router.get(
            "/recent-feedbacks",
            tags=["Feedback Analysis"],
            response_model=List[Feedback]
        )(self.get_recent_feedbacks)
        self.router.get(
            "/rating-sentiment-counts",
            tags=["Feedback Analysis"],
            response_model=RatingSentimentCounts
        )(self.get_rating_sentiment_counts)

    def format_time_elapsed(self, seconds):
        seconds = abs(seconds)
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{int(minutes)} minute{'s' if minutes != 1 else ''}"
        else:
            hours = seconds // 3600
            return f"{int(hours)} hour{'s' if hours != 1 else ''}"

    def get_sentiment_label(self, feedback_text: str) -> str:
        vader_scores = vader.polarity_scores(feedback_text)
        sentiment_score = vader_scores['compound']
        return (
            "positive" if sentiment_score > 0.3 else
            "negative" if sentiment_score < -0.2 else
            "neutral"
        )

    def get_recent_feedbacks(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        current_time = datetime.now()

        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start, "$lte": end}
                }
            },
            {
                "$sort": {"timestamp": -1}
            },
            {
                "$project": {
                    "name": 1,
                    "rating": 1,
                    "feedback": 1,
                    "camera_name": 1,
                    "time_elapsed": {
                        "$divide": [
                            {"$subtract": [current_time, "$timestamp"]},
                            1000
                        ]
                    },
                    "_id": 0
                }
            },
            {
                "$sort": {"camera_name": 1, "name": 1}
            }
        ]

        results = list(feedback_collection.aggregate(pipeline))
        if not results:
            raise HTTPException(status_code=404, detail="No feedback found for today")

        # Add sentiment label and format time_elapsed
        for result in results:
            result["time_elapsed"] = self.format_time_elapsed(result["time_elapsed"])
            result["sentiment_label"] = self.get_sentiment_label(result["feedback"])

        return [Feedback(**r) for r in results]

    def get_rating_sentiment_counts(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)

        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start, "$lte": end}
                }
            },
            {
                "$facet": {
                    "ratings": [
                        {
                            "$group": {
                                "_id": "$rating",
                                "count": {"$sum": 1}
                            }
                        },
                        {
                            "$project": {
                                "rating": "$_id",
                                "count": 1,
                                "_id": 0
                            }
                        }
                    ],
                    "feedbacks": [
                        {
                            "$project": {
                                "feedback": 1
                            }
                        }
                    ]
                }
            }
        ]

        results = list(feedback_collection.aggregate(pipeline))
        if not results:
            raise HTTPException(status_code=404, detail="No feedback data found")

        result = results[0]
        # Process ratings
        ratings = {str(i): 0 for i in range(1, 6)}
        for r in result["ratings"]:
            ratings[str(r["rating"])] = r["count"]

        # Process sentiments
        sentiments = {"positive": 0, "negative": 0, "neutral": 0}
        for feedback in result["feedbacks"]:
            sentiment = self.get_sentiment_label(feedback["feedback"])
            sentiments[sentiment] += 1

        return RatingSentimentCounts(ratings=ratings, sentiments=sentiments)

router = FeedbackAPI().router