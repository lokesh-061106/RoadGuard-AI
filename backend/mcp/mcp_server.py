import os
import sys
import datetime
import math
from typing import Dict, Any, List, Optional

# Add parent directory to sys.path to allow imports from backend/
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from db_manager import db
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("RoadGuard_MCP_Server")

# Tool 1: get_location_context
@mcp.tool()
def get_location_context(latitude: float, longitude: float) -> dict:
    """
    Retrieve location-specific metadata including traffic density, school zone status, 
    road category, population density, and local accident history statistics.
    """
    # Deterministic simulation based on coordinate hashes to represent real geographic mapping
    lat_hash = int(abs(latitude) * 10000)
    lon_hash = int(abs(longitude) * 10000)
    hash_val = lat_hash + lon_hash

    # Assign road category
    road_cats = ["National Highway", "State Highway", "Arterial Road", "Local Road"]
    road_category = road_cats[hash_val % len(road_cats)]

    # Traffic Density
    traffic_densities = ["Low", "Medium", "High"]
    traffic_density = traffic_densities[(hash_val // 2) % len(traffic_densities)]

    # School Zone Status
    school_zone = (hash_val % 7) == 0

    # Accident History Count
    accident_history_count = (hash_val % 11)

    # Population Density
    pop_densities = ["Low", "Medium", "High", "Very High"]
    population_density = pop_densities[(hash_val // 3) % len(pop_densities)]

    return {
        "road_category": road_category,
        "traffic_density": traffic_density,
        "school_zone": school_zone,
        "accident_history_count": accident_history_count,
        "population_density": population_density
    }

# Tool 2: save_incident
@mcp.tool()
def save_incident(incident_data: dict) -> dict:
    """
    Save or update an incident in the central incident registry (incidents.json).
    """
    incidents = db.read('incidents', default=[])
    
    # Check if this is an update or a new insert
    incident_id = incident_data.get("id")
    found_idx = -1
    for idx, inc in enumerate(incidents):
        if inc.get("id") == incident_id:
            found_idx = idx
            break

    current_time = datetime.datetime.utcnow().isoformat() + "Z"
    
    if found_idx >= 0:
        # Update existing
        incident_data["updated_at"] = current_time
        incidents[found_idx] = incident_data
    else:
        # Create new
        incident_data["created_at"] = current_time
        incident_data["updated_at"] = current_time
        incidents.append(incident_data)

    db.write('incidents', incidents)
    return {
        "status": "success",
        "incident_id": incident_id,
        "action": "saved" if found_idx < 0 else "updated"
    }

# Tool 3: get_incident_registry
@mcp.tool()
def get_incident_registry() -> list:
    """
    Retrieve all registered infrastructure incidents.
    """
    return db.read('incidents', default=[])

# Tool 4: award_reward_points
@mcp.tool()
def award_reward_points(user_id: str, points: int, reason: str) -> dict:
    """
    Award civic contribution points to a citizen and log the transaction in rewards.json.
    """
    users = db.read('users', default=[])
    rewards = db.read('rewards', default=[])
    
    user_found = None
    for user in users:
        if user.get("id") == user_id:
            user_found = user
            break
            
    if not user_found:
        return {"status": "error", "message": "User not found"}

    # Update points
    old_points = user_found.get("points", 0)
    new_points = old_points + points
    user_found["points"] = new_points

    # Evaluate new badges based on point milestones
    badges = user_found.get("badges", [])
    new_badge = None
    badge_milestones = [
        (100, "Community Guardian"),
        (200, "Infrastructure Hero"),
        (500, "National Contributor"),
        (1000, "Smart City Champion")
    ]
    
    # Ensure "Road Protector" is given for their first report
    if points > 0 and len(badges) == 0:
        new_badge = "Road Protector"
        badges.append(new_badge)

    for milestone, name in badge_milestones:
        if new_points >= milestone and name not in badges:
            new_badge = name
            badges.append(name)
            
    user_found["badges"] = badges
    db.write('users', users)

    # Log transaction
    tx_id = f"tx_{int(datetime.datetime.utcnow().timestamp() * 1000)}"
    transaction = {
        "id": tx_id,
        "user_id": user_id,
        "type": "earn",
        "points": points,
        "reason": reason,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    rewards.append(transaction)
    db.write('rewards', rewards)

    # Update Leaderboard Cache
    update_leaderboard_cache()

    return {
        "status": "success",
        "user_id": user_id,
        "points_awarded": points,
        "new_balance": new_points,
        "badge_earned": new_badge
    }

# Tool 5: get_user_rewards
@mcp.tool()
def get_user_rewards(user_id: str) -> dict:
    """
    Retrieve rewards profile for a user including point balance, badges, and history.
    """
    users = db.read('users', default=[])
    rewards = db.read('rewards', default=[])
    
    user_found = None
    for u in users:
        if u.get("id") == user_id:
            user_found = u
            break
            
    if not user_found:
        return {"status": "error", "message": "User not found"}

    user_txs = [tx for tx in rewards if tx.get("user_id") == user_id]
    user_txs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {
        "user_id": user_id,
        "name": user_found.get("name"),
        "points": user_found.get("points", 0),
        "badges": user_found.get("badges", []),
        "transactions": user_txs
    }

# Tool 6: generate_city_analytics
@mcp.tool()
def generate_city_analytics() -> dict:
    """
    Perform smart governance processing on all logged incidents to compute severity
    distribution, hot-spots, average risk indices, and budget predictions.
    """
    incidents = db.read('incidents', default=[])
    workorders = db.read('workorders', default=[])
    
    total = len(incidents)
    resolved = sum(1 for inc in incidents if inc.get("status") == "resolved")
    in_progress = sum(1 for inc in incidents if inc.get("status") == "in-progress" or inc.get("status") == "dispatched")
    reported = sum(1 for inc in incidents if inc.get("status") == "reported")

    risk_sum = 0
    risk_count = 0
    
    severity_dist = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    category_dist = {}
    hotspots = []
    
    # Calculate costs
    total_spent = 0
    estimated_outstanding = 0

    for inc in incidents:
        # Severity
        det = inc.get("detection", {})
        sev = det.get("severity", "Low")
        if sev in severity_dist:
            severity_dist[sev] += 1
            
        # Category
        cat = det.get("category", "Uncategorized")
        category_dist[cat] = category_dist.get(cat, 0) + 1

        # Risk
        risk_data = inc.get("risk", {})
        r_score = risk_data.get("risk_score")
        if r_score is not None:
            risk_sum += r_score
            risk_count += 1

        # Hotspots mapping (filter to active high-risk)
        weight = (r_score / 100.0) if r_score else 0.5
        hotspots.append({
            "latitude": inc.get("latitude"),
            "longitude": inc.get("longitude"),
            "weight": weight,
            "description": f"{det.get('damage_type', 'Damage')} ({sev})"
        })

        # Repair cost summing
        rep = inc.get("repair", {})
        cost_str = rep.get("estimated_cost", "$0").replace('$', '').replace(',', '')
        try:
            cost_val = int(cost_str) if cost_str.isdigit() else 0
        except:
            cost_val = 0
            
        if inc.get("status") == "resolved":
            total_spent += cost_val
        else:
            estimated_outstanding += cost_val

    avg_risk = round(risk_sum / risk_count, 1) if risk_count > 0 else 0.0

    analytics_data = {
        "summary": {
            "total_incidents": total,
            "resolved": resolved,
            "in_progress": in_progress,
            "reported": reported,
            "average_risk_score": avg_risk,
            "total_budget_spent": f"${total_spent}",
            "estimated_outstanding_budget": f"${estimated_outstanding}"
        },
        "severity_distribution": severity_dist,
        "category_distribution": category_dist,
        "hotspots": hotspots,
        "monthly_risk_trend": db.read('analytics', {}).get("monthly_risk_trend", [])
    }
    
    db.write('analytics', analytics_data)
    return analytics_data

# Tool 7: get_leaderboard
@mcp.tool()
def get_leaderboard() -> list:
    """
    Get citizen leaderboard sorted by points.
    """
    return db.read('leaderboard', default=[])

# Tool 8: detect_duplicate_reports
@mcp.tool()
def detect_duplicate_reports(latitude: float, longitude: float, damage_type: str) -> dict:
    """
    Detect if an active incident of a similar category already exists within a 50-meter
    radius to prevent duplicate points and redundant maintenance orders.
    """
    incidents = db.read('incidents', default=[])
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        # Radius of the Earth in meters
        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    duplicates = []
    # Maximum matching distance threshold in meters
    THRESHOLD_METERS = 50.0

    for inc in incidents:
        if inc.get("status") == "resolved":
            continue # Resolved issues can be reported again if they reoccur
            
        det = inc.get("detection", {})
        cur_type = det.get("damage_type", "").lower()
        if cur_type == damage_type.lower():
            distance = haversine_distance(latitude, longitude, inc.get("latitude"), inc.get("longitude"))
            if distance <= THRESHOLD_METERS:
                duplicates.append({
                    "id": inc.get("id"),
                    "distance_meters": round(distance, 1),
                    "reporter_name": inc.get("reporter_name"),
                    "status": inc.get("status"),
                    "created_at": inc.get("created_at")
                })

    if duplicates:
        return {
            "duplicate_detected": True,
            "matching_incidents": duplicates
        }
    else:
        return {
            "duplicate_detected": False,
            "matching_incidents": []
        }

# Tool 9: generate_monthly_report
@mcp.tool()
def generate_monthly_report() -> str:
    """
    Generates a smart governance monthly executive briefing outlining safety performance,
    re-solved issues count, expenditure summaries, and hotspot clusters.
    """
    analytics = generate_city_analytics()
    summary = analytics.get("summary", {})
    severity = analytics.get("severity_distribution", {})
    categories = analytics.get("category_distribution", {})
    
    report = f"""# ROADGUARD AI - EXECUTIVE SMART CITY INFRASTRUCTURE BRIEFING
Generated: {datetime.datetime.utcnow().strftime('%B %d, %Y')}
Status: Production Core Summary

## 1. INCIDENT SUMMARIES
* **Total Reported Incidents**: {summary.get('total_incidents', 0)}
* **Resolved / Completed**: {summary.get('resolved', 0)}
* **In Progress / Dispatched**: {summary.get('in_progress', 0)}
* **Pending AI Audit**: {summary.get('reported', 0)}
* **Average Public Danger Index**: {summary.get('average_risk_score', 0.0)}/100

## 2. RISK LEVEL SEGMENTATION
* **Critical Danger Hazards**: {severity.get('Critical', 0)}
* **High Severity Issues**: {severity.get('High', 0)}
* **Medium Severity Incidents**: {severity.get('Medium', 0)}
* **Low Risk Assets**: {severity.get('Low', 0)}

## 3. CATEGORICAL INDEX
"""
    for cat, count in categories.items():
        report += f"* **{cat}**: {count} active incidents\n"

    report += f"""
## 4. FISCAL ANALYSIS & ALLOCATIONS
* **Aggregated Completed Expenditure**: {summary.get('total_budget_spent', '$0')}
* **Outstanding Maintenance Backlog Cost**: {summary.get('estimated_outstanding_budget', '$0')}

---
*RoadGuard AI is optimized for Google Cloud Run and Antigravity Agent framework.*
"""
    return report

def update_leaderboard_cache():
    """Helper function to update leaderboard rankings based on user points."""
    users = db.read('users', default=[])
    citizens = [u for u in users if u.get("role") == "citizen"]
    citizens.sort(key=lambda x: x.get("points", 0), reverse=True)
    
    leaderboard = []
    for idx, c in enumerate(citizens):
        leaderboard.append({
            "user_id": c.get("id"),
            "name": c.get("name"),
            "points": c.get("points", 0),
            "badges": c.get("badges", []),
            "rank": idx + 1
        })
        
    db.write('leaderboard', leaderboard)

if __name__ == '__main__':
    mcp.run()
