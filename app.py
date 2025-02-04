from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import random
import feedparser
import os

app = Flask(__name__)

# API & Data Sources
LEGISCAN_API_KEY = os.getenv("LEGISCAN_API_KEY")
LEGISCAN_BASE_URL = f"https://api.legiscan.com/?key={LEGISCAN_API_KEY}"
SEARCH_TERMS = ["transgender", "gender identity", "LGBTQ", "non-binary", "gender-affirming care"]
CSV_FILE_RESOURCES = "Data/CSV/resources.csv"

# Sample states for Equality Index trends
US_STATES = ["CA", "TX", "NY", "FL", "WA", "OH"]

# Generate sample Equality Index trends
def generate_chart_data(state):
    years = list(range(2015, 2025))
    trend_data = [random.randint(40, 90) for _ in years]

    return {
        "labels": years,
        "datasets": [
            {"label": f"{state} Equality Index", "data": trend_data}
        ],
    }

# Fetch legislative bills dynamically based on selected state
def fetch_trans_bills(state="US"):
    """Fetches transgender-related bills for a given state."""
    all_bills = []
    for term in SEARCH_TERMS:
        response = requests.get(f"{LEGISCAN_BASE_URL}&op=search&q={term}&state={state}")

        try:
            data = response.json()
            search_results = data.get("searchresult", {})
            bills_list = [search_results[key] for key in search_results if key.isdigit()]
            
            for bill in bills_list:
                all_bills.append({
                    "State": bill.get("state", "Unknown"),
                    "Bill Number": bill.get("bill_number", "N/A"),
                    "Title": bill.get("title", "No title available"),
                    "Status": bill.get("last_action", "Unknown"),
                    "Link": bill.get("url", "N/A"),
                })
        except Exception as e:
            print(f"Error fetching bills for {state}: {e}")

    return all_bills

# Fetch LGBTQ+ news
def fetch_lgbtq_news():
    """Fetches latest LGBTQ+ news from an RSS feed."""
    rss_url = "https://www.lgbtqnation.com/feed/"
    news_feed = feedparser.parse(rss_url)

    news_items = []
    for entry in news_feed.entries[:5]:  # Get the latest 5 articles
        news_items.append({
            "title": entry.title,
            "link": entry.link
        })

    return news_items

@app.route('/')
def index():
    """Renders homepage with Equality Index, Bills, Resources, and LGBTQ News."""
    default_state = "US"
    chart_data = generate_chart_data(default_state)
    bills_data = fetch_trans_bills(default_state)

    # Load resources from CSV
    df_resources = pd.read_csv(CSV_FILE_RESOURCES)
    resources_data = df_resources.to_dict(orient="records")

    # Fetch news
    news_data = fetch_lgbtq_news()

    return render_template("index.html", chart_data=chart_data, bills_data=bills_data, resources_data=resources_data, news_data=news_data)

@app.route('/update_chart', methods=['POST'])
def update_chart():
    """Updates the Equality Index chart based on the selected state."""
    state = request.json.get("state", "US")  # Get the selected state
    chart_data = generate_chart_data(state)  # No need to modify state format here
    return jsonify(chart_data)

@app.route('/update_bills', methods=['POST'])
def update_bills():
    """Updates the bills dynamically based on the selected state."""
    state = request.json.get("state", "US")  # Get the selected state

    # Ensure the state format is correct for LegiScan (XX only)
    if state.startswith("US-"):
        state = state.replace("US-", "")

    bills_data = fetch_trans_bills(state)  # Send correct state format
    return jsonify(bills_data)

if __name__ == "__main__":
    app.run(debug=True)
