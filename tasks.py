from typing import List, Dict, Any
from models import Email

def get_easy_task():
    return [
        Email(id="e1", sender="customer@buy.com", subject="Pricing inquiry", body="How much does the enterprise tier cost?"),
        Email(id="e2", sender="staff@company.com", subject="Benefits update", body="Please review the new HR benefits document."),
        Email(id="e3", sender="user@app.com", subject="Password reset not working", body="I cannot reset my password, the link is broken.")
    ]

def get_medium_task():
    return [
        Email(id="m1", sender="scam@free-money.xyz", subject="YOU WON $1000", body="Click here to claim your prize!"),
        Email(id="m2", sender="angry@client.com", subject="URGENT: Server down", body="Our server has been down for 2 hours! Fix this immediately."),
        Email(id="m3", sender="newhire@company.com", subject="Onboarding", body="Where is the HR onboarding packet?"),
        Email(id="m4", sender="buyer@corp.com", subject="Bulk order", body="We want to order 500 licenses of your software."),
        Email(id="m5", sender="user2@app.com", subject="Bug report", body="The checkout button on Chrome is hidden.")
    ]

def get_hard_task():
    return [
        Email(id="h1", sender="lottery@spam.com", subject="Winner", body="Claim your prize!"),
        Email(id="h2", sender="boss@company.com", subject="Important Client", body="VIP client is 'MegaCorp'. Treat their tickets with priority."),
        Email(id="h3", sender="ceo@megacorp.com", subject="Meeting", body="Let's discuss the pricing for the enterprise tier."),
        Email(id="h4", sender="worker@hr-dept.com", subject="Policy update", body="Vacation policy changed."),
        Email(id="h5", sender="crypto@wallet.net", subject="Investment", body="Buy our new coin."),
        Email(id="h6", sender="support@vendor.com", subject="Vendor invoice", body="Please pay the attached invoice."),
        Email(id="h7", sender="random@guy.com", subject="Hello", body="Just saying hi."),
        Email(id="h8", sender="marketing@agency.com", subject="Campaign", body="The new sales campaign is ready."),
        Email(id="h9", sender="dev@team.com", subject="Deploy failed", body="The production deployment has failed."),
        Email(id="h10", sender="phish@fake.com", subject="Reset password", body="Your IT admin asks you to reset your password here: http://fake.com")
    ]

def grade_easy(routed: Dict[str, str], replies: Dict[str, str], spam: set) -> float:
    score = 0.0
    expected = {"e1": "sales", "e2": "hr", "e3": "support"}
    for eid, folder in expected.items():
        if routed.get(eid) == folder:
            score += 1.0
    return score / len(expected)

def grade_medium(routed: Dict[str, str], replies: Dict[str, str], spam: set) -> float:
    score = 0.0
    expected_route = {"m3": "hr", "m4": "sales", "m5": "support"}
    
    # Check routes
    routes_correct = sum(1 for eid, f in expected_route.items() if routed.get(eid) == f)
    score += routes_correct * 0.2
    
    # Check spam
    if "m1" in spam:
        score += 0.2
        
    # Check reply
    if "m2" in replies and len(replies["m2"]) > 5:
        score += 0.2
        
    return min(max(score, 0.0), 1.0)

def grade_hard(routed: Dict[str, str], replies: Dict[str, str], spam: set) -> float:
    score = 0.0
    
    expected_spam = {"h1", "h5", "h10"}
    correct_spam = len(spam.intersection(expected_spam))
    score += correct_spam * 0.1
    
    expected_route = {"h4": "hr", "h6": "support", "h8": "sales", "h9": "support"}
    routes_correct = sum(1 for eid, f in expected_route.items() if routed.get(eid) == f)
    score += routes_correct * 0.1
    
    # Reply to VIP client (MegaCorp)
    if "h3" in replies and len(replies["h3"]) > 10:
        score += 0.3
        
    return min(max(score, 0.0), 1.0)

def get_task_data(task_id: str):
    if task_id == "easy":
        return get_easy_task(), grade_easy
    elif task_id == "medium":
        return get_medium_task(), grade_medium
    elif task_id == "hard":
        return get_hard_task(), grade_hard
    else:
        return get_easy_task(), grade_easy
