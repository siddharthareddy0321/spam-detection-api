import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

data = {
    "message":[
        "Win money now",
        "Hello how are you",
        "Free offer click now",
        "Let's meet tomorrow",
        "Claim your prize now",
        "Good morning friend"
    ],
    "label":[1,0,1,0,1,0]
}

df = pd.DataFrame(data)

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df["message"])
y = df["label"]

model = MultinomialNB()
model.fit(X,y)

pickle.dump(model, open("model.pkl","wb"))
pickle.dump(vectorizer, open("vectorizer.pkl","wb"))

print("Model Trained Successfully")
