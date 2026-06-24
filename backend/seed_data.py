import os
import datetime
from db_manager import db

def seed_all(force: bool = False):
    users = db.read('users')
    
    # Check if database is already populated
    if users and not force:
        print("Database already seeded. Skipping seeding. Use force=True to re-seed.")
        return

    print("Seeding database with default Kaggle Capstone demo records...")

    # 1. Seed Users (citizens, authority, admin)
    users_data = [
        {
            "id": "usr_1",
            "name": "Arjun Kumar",
            "email": "arjun@roadguard.ai",
            "password": "pbkdf2:sha256:260000$defaultpbkdf2hashvaluecitizen1",  # Simple mock hash (we'll support password verification)
            "role": "citizen",
            "points": 185,
            "badges": ["Road Protector", "Community Guardian"],
            "created_at": "2026-06-15T09:00:00Z"
        },
        {
            "id": "usr_2",
            "name": "Priya Sharma",
            "email": "priya@roadguard.ai",
            "password": "pbkdf2:sha256:260000$defaultpbkdf2hashvaluecitizen2",
            "role": "citizen",
            "points": 75,
            "badges": ["Road Protector"],
            "created_at": "2026-06-18T14:30:00Z"
        },
        {
            "id": "usr_3",
            "name": "Officer Vikram Rathore",
            "email": "vikram@roadguard.ai",
            "password": "pbkdf2:sha256:260000$defaultpbkdf2hashvalueauthority",
            "role": "authority",
            "points": 0,
            "badges": [],
            "created_at": "2026-06-10T08:00:00Z"
        },
        {
            "id": "usr_4",
            "name": "Suresh Iyer",
            "email": "suresh@roadguard.ai",
            "password": "pbkdf2:sha256:260000$defaultpbkdf2hashvalueadmin",
            "role": "admin",
            "points": 0,
            "badges": [],
            "created_at": "2026-06-01T10:00:00Z"
        }
    ]
    db.write('users', users_data)

    # 2. Seed Incidents
    incidents_data = [
        {
            "id": "inc_1001",
            "reporter_id": "usr_1",
            "reporter_name": "Arjun Kumar",
            "image_name": "pothole_nh44.jpg",
            "image_url": "/static/images/pothole_nh44.jpg",
            "description": "Large pothole in the middle lane of NH-44 near Hebbal, causing vehicles to swerve suddenly.",
            "latitude": 13.0358,
            "longitude": 77.5978,
            "status": "in-progress",
            "location_context": {
                "road_category": "National Highway",
                "traffic_density": "High",
                "school_zone": False,
                "accident_history_count": 8,
                "population_density": "High"
            },
            "detection": {
                "damage_type": "Pothole",
                "severity": "High",
                "confidence": "94%",
                "category": "Road Damage"
            },
            "risk": {
                "risk_score": 85,
                "priority": "Critical",
                "explanation": "Pothole is located on a High Traffic National Highway with a history of recurrent accidents."
            },
            "repair": {
                "repair_method": "Hot-mix asphalt filling with mechanical compaction",
                "materials": ["Asphalt concrete", "Tack coat", "Bituminous sealant"],
                "estimated_cost": "$450",
                "estimated_duration": "4 hours"
            },
            "dispatch": {
                "incident_id": "inc_1001",
                "status": "Dispatched",
                "department": "National Highways Authority",
                "work_order_id": "wo_99201"
            },
            "reward": {
                "reward_points": 50,
                "badge_awarded": None
            },
            "created_at": "2026-06-20T12:00:00Z",
            "updated_at": "2026-06-20T12:05:00Z"
        },
        {
            "id": "inc_1002",
            "reporter_id": "usr_2",
            "reporter_name": "Priya Sharma",
            "image_name": "streetlight_whitefield.jpg",
            "image_url": "/static/images/streetlight_whitefield.jpg",
            "description": "Broken streetlight pole at ITPL main road junction. Dangerous at night.",
            "latitude": 12.9842,
            "longitude": 77.7289,
            "status": "resolved",
            "location_context": {
                "road_category": "Arterial Road",
                "traffic_density": "Medium",
                "school_zone": True,
                "accident_history_count": 2,
                "population_density": "High"
            },
            "detection": {
                "damage_type": "Streetlight Failure",
                "severity": "Medium",
                "confidence": "89%",
                "category": "Electrical / Lighting"
            },
            "risk": {
                "risk_score": 60,
                "priority": "High",
                "explanation": "Streetlight failure located in a school zone with medium traffic, increasing pedestrian hazards at night."
            },
            "repair": {
                "repair_method": "Replacement of LED luminaire and pole rewiring",
                "materials": ["120W LED streetlight fixture", "Anchor bolts", "Electrical cable"],
                "estimated_cost": "$280",
                "estimated_duration": "2 hours"
            },
            "dispatch": {
                "incident_id": "inc_1002",
                "status": "Completed",
                "department": "Municipal Electricity Department",
                "work_order_id": "wo_99202"
            },
            "reward": {
                "reward_points": 25,
                "badge_awarded": "Road Protector"
            },
            "created_at": "2026-06-21T18:30:00Z",
            "updated_at": "2026-06-22T10:00:00Z"
        },
        {
            "id": "inc_1003",
            "reporter_id": "usr_1",
            "reporter_name": "Arjun Kumar",
            "image_name": "drainage_koramangala.jpg",
            "image_url": "/static/images/drainage_koramangala.jpg",
            "description": "Clogged drainage inlet causing severe waterlogging across two lanes near St. John's hospital.",
            "latitude": 12.9344,
            "longitude": 77.6206,
            "status": "dispatched",
            "location_context": {
                "road_category": "Arterial Road",
                "traffic_density": "High",
                "school_zone": False,
                "accident_history_count": 4,
                "population_density": "Very High"
            },
            "detection": {
                "damage_type": "Drainage Clog",
                "severity": "Critical",
                "confidence": "96%",
                "category": "Sanitation & Drainage"
            },
            "risk": {
                "risk_score": 92,
                "priority": "Critical",
                "explanation": "Critical drainage failure causing road inundation adjacent to a major hospital zone with very high population density."
            },
            "repair": {
                "repair_method": "High-pressure hydro-jetting and silt extraction",
                "materials": ["De-silting equipment", "Gully grate replacement"],
                "estimated_cost": "$600",
                "estimated_duration": "6 hours"
            },
            "dispatch": {
                "incident_id": "inc_1003",
                "status": "Dispatched",
                "department": "Stormwater Drainage Dept",
                "work_order_id": "wo_99203"
            },
            "reward": {
                "reward_points": 100,
                "badge_awarded": "Community Guardian"
            },
            "created_at": "2026-06-23T07:15:00Z",
            "updated_at": "2026-06-23T08:00:00Z"
        },
        {
            "id": "inc_1004",
            "reporter_id": "usr_2",
            "reporter_name": "Priya Sharma",
            "image_name": "signboard_orr.jpg",
            "image_url": "/static/images/signboard_orr.jpg",
            "description": "Speed limit signboard is bent and lying on the sidewalk near Bellandur pedestrian bridge.",
            "latitude": 12.9279,
            "longitude": 77.6811,
            "status": "reported",
            "location_context": {
                "road_category": "State Highway",
                "traffic_density": "High",
                "school_zone": False,
                "accident_history_count": 1,
                "population_density": "High"
            },
            "detection": {
                "damage_type": "Damaged Signboard",
                "severity": "Low",
                "confidence": "91%",
                "category": "Traffic Signage"
            },
            "risk": {
                "risk_score": 35,
                "priority": "Low",
                "explanation": "Damaged speed limit sign is lying safely on the sidewalk, representing low immediate safety hazard."
            },
            "repair": {
                "repair_method": "Post re-installation and concrete reinforcement",
                "materials": ["Steel mounting brackets", "Concrete mix", "Fasteners"],
                "estimated_cost": "$120",
                "estimated_duration": "1.5 hours"
            },
            "dispatch": {
                "incident_id": "inc_1004",
                "status": "Pending Review",
                "department": "Traffic Management Agency",
                "work_order_id": None
            },
            "reward": {
                "reward_points": 10,
                "badge_awarded": None
            },
            "created_at": "2026-06-24T10:00:00Z",
            "updated_at": "2026-06-24T10:05:00Z"
        }
    ]
    db.write('incidents', incidents_data)

    # 3. Seed Rewards Transactions
    rewards_data = [
        {
            "id": "tx_2001",
            "user_id": "usr_1",
            "type": "earn",
            "points": 50,
            "reason": "Verified High Severity Pothole Report",
            "timestamp": "2026-06-20T12:05:00Z"
        },
        {
            "id": "tx_2002",
            "user_id": "usr_2",
            "type": "earn",
            "points": 25,
            "reason": "Verified Medium Severity Streetlight Failure Report",
            "timestamp": "2026-06-22T10:00:00Z"
        },
        {
            "id": "tx_2003",
            "user_id": "usr_1",
            "type": "earn",
            "points": 100,
            "reason": "Verified Critical Drainage Clog Report",
            "timestamp": "2026-06-23T08:00:00Z"
        },
        {
            "id": "tx_2004",
            "user_id": "usr_2",
            "type": "earn",
            "points": 10,
            "reason": "Verified Low Severity Damaged Signboard Report",
            "timestamp": "2026-06-24T10:05:00Z"
        },
        {
            "id": "tx_2005",
            "user_id": "usr_1",
            "type": "redeem",
            "points": 40,
            "reward_name": "Public Transport Credit ($5 Value) - SIMULATION",
            "timestamp": "2026-06-24T12:00:00Z"
        },
        {
            "id": "tx_2006",
            "user_id": "usr_2",
            "type": "earn",
            "points": 40,
            "reason": "Initial Registration Reward",
            "timestamp": "2026-06-18T14:30:00Z"
        },
        {
            "id": "tx_2007",
            "user_id": "usr_1",
            "type": "earn",
            "points": 75,
            "reason": "Consistent Weekly Patrol Bonus",
            "timestamp": "2026-06-23T18:00:00Z"
        }
    ]
    db.write('rewards', rewards_data)

    # 4. Seed Work Orders
    workorders_data = [
        {
            "id": "wo_99201",
            "incident_id": "inc_1001",
            "department": "National Highways Authority",
            "urgency": "Critical",
            "details": "Dispatch road maintenance truck with hot asphalt compound. Fill center lane pothole at NH-44 coordinate (13.0358, 77.5978). Use mechanical rolling compactors. Divert middle lane traffic during compaction.",
            "estimated_cost": "$450",
            "status": "Dispatched",
            "assigned_crew": "Crew B (Hebbal Sector)",
            "created_at": "2026-06-20T12:05:00Z",
            "completed_at": None
        },
        {
            "id": "wo_99202",
            "incident_id": "inc_1002",
            "department": "Municipal Electricity Department",
            "urgency": "High",
            "details": "Replace 120W LED luminaire bulb on pole #E32, ITPL main road junction. Run diagnostic check on wiring conduit for line leakage.",
            "estimated_cost": "$280",
            "status": "Completed",
            "assigned_crew": "Crew E-Light",
            "created_at": "2026-06-21T18:35:00Z",
            "completed_at": "2026-06-22T10:00:00Z"
        },
        {
            "id": "wo_99203",
            "incident_id": "inc_1003",
            "department": "Stormwater Drainage Dept",
            "urgency": "Critical",
            "details": "Clogged drainage inlet near St. John's hospital coordinates (12.9344, 77.6206) causing street flooding. Dispatch suction/hydro-jetting vehicle. Clean out concrete debris and silt. Replace damaged gully grate.",
            "estimated_cost": "$600",
            "status": "Dispatched",
            "assigned_crew": "Hydro-Vac Crew 4",
            "created_at": "2026-06-23T08:00:00Z",
            "completed_at": None
        }
    ]
    db.write('workorders', workorders_data)

    # 5. Seed Leaderboard
    leaderboard_data = [
        {
            "user_id": "usr_1",
            "name": "Arjun Kumar",
            "points": 185,
            "badges": ["Road Protector", "Community Guardian"],
            "rank": 1
        },
        {
            "user_id": "usr_2",
            "name": "Priya Sharma",
            "points": 75,
            "badges": ["Road Protector"],
            "rank": 2
        }
    ]
    db.write('leaderboard', leaderboard_data)

    # 6. Seed Analytics
    analytics_data = {
        "summary": {
            "total_incidents": 4,
            "resolved": 1,
            "in_progress": 2,
            "reported": 1,
            "average_risk_score": 68.0,
            "total_budget_spent": "$280",
            "estimated_outstanding_budget": "$1170"
        },
        "severity_distribution": {
            "Critical": 1,
            "High": 1,
            "Medium": 1,
            "Low": 1
        },
        "category_distribution": {
            "Road Damage": 1,
            "Electrical / Lighting": 1,
            "Sanitation & Drainage": 1,
            "Traffic Signage": 1
        },
        "hotspots": [
            {"latitude": 13.0358, "longitude": 77.5978, "weight": 0.85, "description": "Pothole (NH-44)"},
            {"latitude": 12.9842, "longitude": 77.7289, "weight": 0.60, "description": "Streetlight Failure (Whitefield)"},
            {"latitude": 12.9344, "longitude": 77.6206, "weight": 0.92, "description": "Drainage Clog (Koramangala)"},
            {"latitude": 12.9279, "longitude": 77.6811, "weight": 0.35, "description": "Signboard Damaged (ORR)"}
        ],
        "monthly_risk_trend": [
            {"month": "January", "risk_index": 45},
            {"month": "February", "risk_index": 50},
            {"month": "March", "risk_index": 42},
            {"month": "April", "risk_index": 55},
            {"month": "May", "risk_index": 60},
            {"month": "June", "risk_index": 68}
        ]
    }
    db.write('analytics', analytics_data)
    print("Database seeding completed successfully.")

if __name__ == '__main__':
    seed_all(force=True)
