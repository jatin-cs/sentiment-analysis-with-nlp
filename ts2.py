import pandas as pd
import re
import string
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.utils import resample
import pickle

# STEP 1: LOAD DATA
df = pd.read_csv('amazon_review.csv')  # replace with your dataset path

# STEP 2: CREATE SENTIMENT LABEL
df['Sentiment'] = df['overall'].apply(lambda x: 1 if x > 3 else 0)

# STEP 3: BALANCE DATASET
df_pos = df[df['Sentiment'] == 1]
df_neg = df[df['Sentiment'] == 0]

df_pos_down = resample(df_pos, replace=False, n_samples=len(df_neg), random_state=42)
df_balanced = pd.concat([df_neg, df_pos_down]).sample(frac=1, random_state=42).reset_index(drop=True)

# STEP 4: IMPROVED NEGATION HANDLING
def handle_negation(text):
    words = text.split()
    result = []
    negate = False
    for word in words:
        lower_word = word.lower()
        if lower_word in ["not", "no", "n't"]:
            negate = True
            result.append("NOT")
        elif negate:
            # Stop negation tagging at punctuation or conjunction
            if re.match(r'[\.\,\;\:\!\?]', word) or lower_word in ['but', 'and', 'or', 'yet', 'so']:
                negate = False
                result.append(word)
            else:
                result.append("NOT_" + word)
        else:
            result.append(word)
    return ' '.join(result)

def clean_text(text):
    text = str(text).lower()
    text = handle_negation(text)  # Negation tagging first
    text = re.sub(f"[{re.escape(string.punctuation)}]", "", text)  # then remove punctuation
    return text

df_balanced['cleaned'] = df_balanced['reviewText'].apply(clean_text)

#  STEP 5: TRAIN-TEST SPLIT
X_train, X_test, y_train, y_test = train_test_split(
    df_balanced['cleaned'], df_balanced['Sentiment'], test_size=0.2, random_state=42
)

# STEP 6: TF-IDF VECTORIZE
tfidf = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf = tfidf.transform(X_test)

# STEP 7: TRAIN MODEL
model = LogisticRegression(max_iter=500)
model.fit(X_train_tfidf, y_train)

# STEP 8: EVALUATE MODEL
y_pred = model.predict(X_test_tfidf)
print(classification_report(y_test, y_pred))

# STEP 9: SAVE MODEL & VECTORIZER
with open('sentiment_model.pkl', 'wb') as f:
    pickle.dump(model, f)
with open('tfidf_vectorizer.pkl', 'wb') as f:
    pickle.dump(tfidf, f)

# STEP 10: PREDICTION FUNCTION
def predict_sentiment(text):
    cleaned = clean_text(text)
    vector = tfidf.transform([cleaned])
    pred = model.predict(vector)[0]
    return "Positive" if pred == 1 else "Negative"

# STEP 11: TEST EXAMPLES
examples = [
    "good",
    "bad",
    "not good",
    "not bad",
    "this product is bad",
    "this product is not good",
    "i am happy",
    "i am not happy",
    "no value for money",
    "this is not worth it",
    "the movie was not interesting but the soundtrack was great",
    "I don't like this product",
    "I do not recommend this",
]

print("\nSample Predictions:")
for example in examples:
    print(f"{example} → {predict_sentiment(example)}")

import re
import string
import pickle

# Load saved model and vectorizer
with open('sentiment_model.pkl', 'rb') as f:
    model = pickle.load(f)

with open('tfidf_vectorizer.pkl', 'rb') as f:
    tfidf = pickle.load(f)

# Same improved negation handling as training
def handle_negation(text):
    words = text.split()
    result = []
    negate = False
    for word in words:
        lower_word = word.lower()
        if lower_word in ["not", "no", "n't"]:
            negate = True
            result.append("NOT")
        elif negate:
            if re.match(r'[\.\,\;\:\!\?]', word) or lower_word in ['but', 'and', 'or', 'yet', 'so']:
                negate = False
                result.append(word)
            else:
                result.append("NOT_" + word)
        else:
            result.append(word)
    return ' '.join(result)

def clean_text(text):
    text = text.lower()
    text = handle_negation(text)
    text = re.sub(f"[{re.escape(string.punctuation)}]", "", text)
    return text

def predict_sentiment(text):
    cleaned = clean_text(text)
    vector = tfidf.transform([cleaned])
    pred = model.predict(vector)[0]
    return "Positive" if pred == 1 else "Negative"

# Interactive loop to test input sentences
while True:
    user_input = input("\nEnter your review text (or type 'exit' to quit): ")
    if user_input.lower() == 'exit':
        print("Exiting.")
        break
    print("Predicted Sentiment:", predict_sentiment(user_input))
