import os
import json
import urllib.request
import urllib.error
from datetime import datetime

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

ACCOUNTS = [
    "Atmosphere", "Bounce Curl CA", "Edloe Finch", "Endy US", "Globein Canada",
    "Hours Collection UK", "Pieratt's", "U Beauty CA", "U Beauty UK", "Aesop Rock",
    "ALLMAG Auto Parts", "ArcticCatPartsHouse", "Body Art Forms Canada", "Burlebo",
    "Buy and Sell Fitness", "Carex Health Brands", "Carrera", "Combat Corner",
    "compcams.com", "Conner Hats", "DeanSafe", "Drag Cartel", "Dr Locs",
    "Foundry Lighting", "Furls Fiberarts", "Garden for Wildlife",
    "Gardner's Wisconsin Cheese", "GASDRAWLS", "Gone for a Run", "Her View From Home",
    "Holistic Habitat Ethical Decor", "Hours Collection CA", "Independent Trading Company",
    "Jean Dousset", "Jeep World", "Living Grace", "Mammoth Headwear",
    "Miansai Australia", "Miansai UK", "Mineral Tiles", "MKF Collection by Mia K",
    "Modern and Chic Boutique", "nuuds", "Once Upon A Book Club", "Parcil Safety",
    "Pathwater", "Positive Grid Canada", "Positive Grid UK", "Sawyer Twain",
    "Senpai Squad", "Shrimpy Biz LLC", "Spiritual and Paid", "Sucreabeille",
    "Terra Health Essentials", "TerrorThreads", "The Hollow Squad", "TTDeye Canada",
    "Voss Helmets", "Agilite", "Albany Park", "Army Surplus World", "Ashimary Hair",
    "BAGSMART", "Bandit", "Blackwell's Wines & Spirits", "BLANK", "Bounce Curl",
    "BrainMD", "Clearly Filtered", "Coros Wearables", "Dr. Harvey's Dog Food",
    "DX Engineering", "Endy", "Hours Collection US", "Ironman 4x4", "Jammers",
    "Jenny Yoo", "Jewelry Candles", "League Outfitters", "Lewkin", "Lifepro fitness",
    "Madison Seating", "Maniology", "Manitobah Mukluks", "Miansai", "Moe Flavor",
    "My Eye BB", "Naked Wardrobe Canada", "Nerdwax", "Nick's Swedish Style Ice Cream AU",
    "Olivia Mark", "PAP MD", "Power Step", "Province of Canada", "Ridge Merino",
    "Sistabag", "SpeakOut Wireless", "Stone & Tile Shoppe", "The Tree Center",
    "Tracksmith", "Trainworld", "True Sea Moss", "TTDeye", "U Beauty", "UDEL",
    "Ultra PRO International LLC", "Undefeated", "Vrsgs", "XPLR", "Ywigs",
    "Moco Boutique", "ban.do France", "ban.do Ireland", "ban.do Italy",
    "ban.do Netherlands", "ban.do Portugal", "CV Linens France", "CV Linens Portugal",
    "Dango Products France", "Dango Products Ireland", "Dango Products Italy",
    "Dango Products Netherlands", "Dango Products Portugal", "Dango Products Spain",
    "Jewelry By Johan Australia", "Jimmy Beans Wool Ireland", "Jimmy Beans Wool Netherlands",
    "Jimmy Beans Wool Spain", "Jimmy Beans Wool Sweden", "Mack Weldon Canada",
    "Mack Weldon France", "Mack Weldon Italy", "Mack Weldon Netherlands",
    "Mack Weldon Spain", "Mack Weldon Sweden", "MadelineTosh France",
    "Melissa Shoes Australia", "Mountain Crest Gardens Canada",
    "Mountain Crest Gardens France", "Mountain Crest Gardens Netherlands",
    "Nationwide Coin & Bullion Reserve Ireland", "Nationwide Coin & Bullion Reserve Sweden",
    "No Cow Ireland", "NOVICA Canada", "NOVIFrance", "NOVIIreland", "NOVINetherlands",
    "NOVISpain", "NOVISweden", "Parks Project Canada", "Refrigiwear Italy",
    "Segway Australia", "Segway Canada", "Suit Shop France", "Suit Shop Ireland",
    "Suit Shop Italy", "Suit Shop Netherlands", "Suit Shop Sweden",
    "The Tree Center Canada", "Undefeated UK"
]

# Rotate through all accounts over ~20 days, ~8 accounts/day
def get_todays_accounts():
    day_of_year = datetime.now().timetuple().tm_yday
    batch_size = 8
    start = (day_of_year * batch_size) % len(ACCOUNTS)
    batch = ACCOUNTS[start:start + batch_size]
    if len(batch) < batch_size:
        batch += ACCOUNTS[:batch_size - len(batch)]
    return batch

def call_anthropic(prompt):
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "interleaved-thinking-2025-05-14"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def post_to_slack(text):
    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read()

def run_digest():
    accounts = get_todays_accounts()
    today = datetime.now().strftime("%A, %B %-d, %Y")
    account_list = ", ".join(accounts)

    print(f"Running digest for: {account_list}")

    prompt = f"""You are a sales intelligence assistant for Tom Kane, a Mid-Market AE.

Search for news from the last 7 days about these DTC/ecommerce accounts: {account_list}

Look for: funding rounds, M&A, leadership changes, product launches, earnings, regulatory news, industry research, and notable social media moments.

For each account where you find real, notable news, return a JSON array. No markdown, no preamble, just the raw JSON array.

Each item:
{{
  "account": "Account Name",
  "signal": "funding|leadership|product|earnings|regulatory|research|social",
  "headline": "Short headline under 12 words",
  "summary": "2-3 sentences: what happened and why it matters for a B2B SaaS sale",
  "hook": "One sentence email opener referencing this news"
}}

Only include accounts with genuine recent news. If nothing notable, return [].
Return ONLY the JSON array, nothing else."""

    data = call_anthropic(prompt)

    results = []
    for block in data.get("content", []):
        if block.get("type") == "text":
            text = block["text"].strip()
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1:
                try:
                    results = json.loads(text[start:end+1])
                except json.JSONDecodeError:
                    pass
            break

    emoji_map = {
        "funding": "💰", "leadership": "👤", "product": "🚀",
        "earnings": "📊", "regulatory": "⚖️", "research": "🔬",
        "social": "📣", "general": "📰"
    }
    label_map = {
        "funding": "Funding / M&A", "leadership": "Leadership change",
        "product": "Product launch", "earnings": "Earnings",
        "regulatory": "Regulatory", "research": "Research",
        "social": "Social signal", "general": "News"
    }

    if not results:
        message = (
            f"📬 *Territory Digest — {today}*\n"
            f"*Tom Kane · Mid-Market*\n"
            f"_Accounts checked: {account_list}_\n\n"
            f"No notable signals today for this batch."
        )
    else:
        lines = [
            f"📬 *Territory Digest — {today}*",
            f"*Tom Kane · Mid-Market*",
            f"_Accounts checked: {account_list}_\n"
        ]
        for r in results:
            e = emoji_map.get(r.get("signal", ""), "📰")
            lbl = label_map.get(r.get("signal", ""), "News")
            lines.append(f"{e} *{r['account']}* · _{lbl}_")
            lines.append(f">{r['headline']}")
            lines.append(f">{r['summary']}")
            lines.append(f">💬 _{r['hook']}_\n")
        message = "\n".join(lines)

    post_to_slack(message)
    print("Posted to Slack successfully.")
    print(f"Found {len(results)} signals.")

if __name__ == "__main__":
    run_digest()
