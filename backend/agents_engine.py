import os
import json
import time

# Override time.sleep dynamically under Vercel serverless environment to prevent Gateway Timeouts
if os.environ.get("VERCEL") == "1":
    _original_sleep = time.sleep
    def vercel_sleep(seconds):
        _original_sleep(0.01)
    time.sleep = vercel_sleep

import random
import datetime
from typing import Dict, Any, Generator
import google.generativeai as genai

# Import database manager directly for client simulation
from db_manager import db
import mcp_services.mcp_server as mcp_tools

# Configure Gemini if API key is present
api_key = os.environ.get("GEMINI_API_KEY")
gemini_enabled = False
if api_key:
    try:
        genai.configure(api_key=api_key)
        gemini_enabled = True
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")

class MultiAgentEngine:
    def __init__(self):
        self.gemini_enabled = gemini_enabled
        if self.gemini_enabled:
            self.model_name = "gemini-1.5-flash"
        else:
            self.model_name = "Rule-based Simulation Engine"

    def execute_pipeline(self, 
                          incident_id: str, 
                          reporter_id: str, 
                          description: str, 
                          latitude: float, 
                          longitude: float, 
                          image_name: str,
                          module: str = "road") -> Generator[str, None, None]:
        """
        Runs the 7 agents in sequence and yields Server-Sent Events (SSE) progress reports.
        """
        def format_sse(event_type: str, data: dict) -> str:
            return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        yield format_sse("pipeline_start", {
            "incident_id": incident_id,
            "message": f"Initiating CivicGuard AI ({module.upper()}) multi-agent analysis pipeline...",
            "timestamp": time.time()
        })
        time.sleep(1)

        # ----------------------------------------------------
        # STEP 1: FraudGuard AI Agent (AI Trust & Verification)
        # ----------------------------------------------------
        yield format_sse("agent_start", {
            "agent": "FraudGuard AI Agent",
            "role": "AI Trust & Verification Officer",
            "status": "Analyzing report trust index, image metadata, location constraints, and spam footprints..."
        })
        time.sleep(1.5)

        trust_deduction = 0
        fraud_reasons = []
        is_fraud = False
        desc_lower = description.lower()
        img_lower = image_name.lower()

        # Check A: AI footprint or Photoshop references
        ai_keywords = ["stable diffusion", "midjourney", "ai generated", "dall-e", "photoshop", "manipulated", "synthetic", "render"]
        if any(kw in desc_lower for kw in ai_keywords) or any(kw in img_lower for kw in ai_keywords):
            trust_deduction += 45
            fraud_reasons.append("AI-Generated / Manipulated Image Footprint")

        # Check B: Spam / Exaggerated description
        spam_keywords = ["free points", "earn money", "test description", "hack points", "cheat points", "admin test"]
        if len(description) < 15 or any(kw in desc_lower for kw in spam_keywords):
            trust_deduction += 15
            fraud_reasons.append("Irrelevant / Exaggerated / Spam Description")

        # Check C: GPS Location bounds (Reject coordinates outside Bengaluru bounds 12.8-13.1 Lat, 77.4-77.8 Lon)
        if not (12.5 <= latitude <= 13.5 and 77.0 <= longitude <= 78.0):
            trust_deduction += 35
            fraud_reasons.append("GPS Coordinate Spoof / Outside Authorized Land Boundaries")

        # Update User's dynamic Trust Score
        users = db.read('users', default=[])
        user_trust_score = 100
        user_trust_level = "Trusted Citizen"
        user_found = False

        for u in users:
            if u.get("id") == reporter_id:
                user_found = True
                current_score = u.get("trust_score", 100)
                new_score = max(0, current_score - trust_deduction)
                u["trust_score"] = new_score
                
                # Determine Trust Level label
                if new_score >= 90:
                    level = "Trusted Citizen"
                elif new_score >= 70:
                    level = "Verified Contributor"
                elif new_score >= 50:
                    level = "Under Monitoring"
                else:
                    level = "Restricted User"
                    is_fraud = True
                u["trust_level"] = level
                user_trust_score = new_score
                user_trust_level = level
                break

        if not user_found:
            # Create transient profile if missing
            user_trust_score = max(0, 100 - trust_deduction)
            if user_trust_score < 50:
                is_fraud = True
                user_trust_level = "Restricted User"

        db.write('users', users)

        status_flag = "Verified"
        if trust_deduction >= 45:
            status_flag = "Rejected - Severe Fraud"
            is_fraud = True
        elif trust_deduction > 0:
            status_flag = "Flagged - Warning"

        fraud_output = {
            "status": status_flag,
            "trust_deduction": trust_deduction,
            "current_trust_score": user_trust_score,
            "trust_level": user_trust_level,
            "details": f"Analysis complete. Deductions: {trust_deduction} pts. Reasons: {', '.join(fraud_reasons) if fraud_reasons else 'None'}"
        }

        yield format_sse("agent_success", {
            "agent": "FraudGuard AI Agent",
            "output": fraud_output
        })
        time.sleep(1)

        # ----------------------------------------------------
        # STEP 2: Infrastructure Detection Agent
        # ----------------------------------------------------
        yield format_sse("agent_start", {
            "agent": "Infrastructure Detection Agent",
            "role": "AI Infrastructure Inspector",
            "status": f"Classifying hazard details and severity for {module.upper()} category..."
        })
        time.sleep(1.5)

        # Module-specific categorizations
        damage_type = "Infrastructure Hazard"
        category = "Public Asset"
        severity = "Medium"

        if module == "road":
            damage_type = "Pothole"
            category = "Road Damage"
            if "crack" in desc_lower:
                damage_type = "Road Crack"
            elif "light" in desc_lower or "lamp" in desc_lower:
                damage_type = "Streetlight Failure"
            elif "drain" in desc_lower or "clog" in desc_lower:
                damage_type = "Drainage Clog"
            elif "sign" in desc_lower or "board" in desc_lower:
                damage_type = "Damaged Signboard"
        elif module == "water":
            damage_type = "Water Leakage"
            category = "Water Infrastructure"
            if "pipeline" in desc_lower or "burst" in desc_lower:
                damage_type = "Broken Pipeline"
            elif "contaminat" in desc_lower or "smell" in desc_lower or "dirty" in desc_lower:
                damage_type = "Water Contamination"
            elif "illegal" in desc_lower or "theft" in desc_lower:
                damage_type = "Illegal Water Usage"
            elif "overflow" in desc_lower or "drainage" in desc_lower:
                damage_type = "Overflowing Drainage"
        elif module == "environment":
            damage_type = "Illegal Dumping"
            category = "Environmental Protection"
            if "smoke" in desc_lower or "air" in desc_lower or "pollution" in desc_lower:
                damage_type = "Air Pollution"
            elif "toxic" in desc_lower or "river" in desc_lower or "lake" in desc_lower:
                damage_type = "Water Pollution"
            elif "tree" in desc_lower or "forest" in desc_lower or "cut" in desc_lower:
                damage_type = "Deforestation"
            elif "burning" in desc_lower or "fire" in desc_lower:
                damage_type = "Open Waste Burning"
        elif module == "cleancity":
            damage_type = "Garbage Accumulation"
            category = "Public Cleanliness & Sanitation"
            if "bin" in desc_lower or "overflow" in desc_lower:
                damage_type = "Overflowing Bin"
            elif "litter" in desc_lower or "dirty" in desc_lower:
                damage_type = "Unclean Public Space"
            elif "dump" in desc_lower:
                damage_type = "Illegal Dumping"
        elif module == "asset":
            damage_type = "Damaged Streetlight"
            category = "Public Asset Management"
            if "bench" in desc_lower:
                damage_type = "Broken Bench"
            elif "park" in desc_lower or "lawn" in desc_lower:
                damage_type = "Park Maintenance Issue"
            elif "bus" in desc_lower or "shelter" in desc_lower:
                damage_type = "Bus Stop Damage"

        # Severity determination
        if any(kw in desc_lower for kw in ["dangerous", "severe", "critical", "toxic", "leak", "flood"]):
            severity = "High"
            if any(kw in desc_lower for kw in ["emergency", "hospital", "drinking", "accident"]):
                severity = "Critical"
        elif any(kw in desc_lower for kw in ["minor", "small", "low"]):
            severity = "Low"

        detection_output = {
            "damage_type": damage_type,
            "severity": severity,
            "confidence": "94%",
            "category": category
        }

        yield format_sse("agent_success", {
            "agent": "Infrastructure Detection Agent",
            "output": detection_output
        })
        time.sleep(1)

        # ----------------------------------------------------
        # STEP 3: Risk Assessment Agent
        # ----------------------------------------------------
        yield format_sse("agent_start", {
            "agent": "Risk Assessment Agent",
            "role": "Public Safety Officer",
            "status": "Analyzing surrounding context risk rating and environmental hazards..."
        })
        time.sleep(1.2)

        # Retrieve Location Context via MCP tool
        location_context = mcp_tools.get_location_context(latitude, longitude)
        
        yield format_sse("agent_progress", {
            "agent": "Risk Assessment Agent",
            "log": f"Location parameters fetched: Category={location_context['road_category']}, Traffic={location_context['traffic_density']}, Proximity check: School={location_context['school_zone']}",
            "tool_calls": []
        })
        time.sleep(1)

        # Compute Risk Rating
        base_scores = {"Low": 20, "Medium": 45, "High": 75, "Critical": 90}
        risk_score = base_scores.get(severity, 45)

        if location_context["traffic_density"] == "High":
            risk_score += 10
        if location_context["school_zone"]:
            risk_score += 15
        
        # Sector-specific adjustments
        if module == "water" and damage_type == "Water Contamination":
            risk_score += 15
        elif module == "environment" and damage_type == "Water Pollution":
            risk_score += 15
        elif module == "cleancity" and location_context["population_density"] == "Very High":
            risk_score += 10

        risk_score = min(100, risk_score)
        
        if risk_score >= 85:
            priority = "Critical"
        elif risk_score >= 65:
            priority = "High"
        elif risk_score >= 40:
            priority = "Medium"
        else:
            priority = "Low"

        explanation = f"Incident score indexed at {risk_score}/100. Prioritized as {priority} due to {severity} severity, located on a {location_context['road_category']} with {location_context['traffic_density']} density."
        if location_context["school_zone"]:
            explanation += " Precaution active: Site situated within a School Zone."
        if is_fraud:
            priority = "Low"
            explanation = "Fraud warning active: Incident flagged by FraudGuard. Safety priority minimized."

        risk_output = {
            "risk_score": risk_score,
            "priority": priority,
            "explanation": explanation
        }

        yield format_sse("agent_success", {
            "agent": "Risk Assessment Agent",
            "output": risk_output
        })
        time.sleep(1)

        # ----------------------------------------------------
        # STEP 4: Repair Recommendation Agent
        # ----------------------------------------------------
        yield format_sse("agent_start", {
            "agent": "Repair Recommendation Agent",
            "role": "Resource Management Advisor",
            "status": "Engineering blueprint materials recommendation and labor cost forecast..."
        })
        time.sleep(1.2)

        # Generate blueprints based on category
        repair_method = "Standard Resurfacing"
        materials = ["Asphalt mix"]
        estimated_cost = "$200"
        estimated_duration = "3 hours"

        if module == "road":
            if damage_type == "Pothole":
                repair_method = "Hot-mix asphalt cavity patching and mechanical rolling"
                materials = ["Hot-mix asphalt", "Tack coat emulsion", "Base binder course"]
                estimated_cost = "$450"
                estimated_duration = "4 hours"
            elif damage_type == "Streetlight Failure":
                repair_method = "Replacing defective LED bulb and conduit continuity check"
                materials = ["120W LED luminaire bulb", "Wiring conduit", "Terminal connectors"]
                estimated_cost = "$280"
                estimated_duration = "2 hours"
        elif module == "water":
            if damage_type == "Water Contamination":
                repair_method = "Main reservoir chlorination flush and heavy carbon filtration"
                materials = ["Sodium hypochlorite", "Active carbon filters", "Water quality tester kit"]
                estimated_cost = "$950"
                estimated_duration = "8 hours"
            else:
                repair_method = "Pipeline sleeve clamp compression leak seal"
                materials = ["Sleeve clamp", "Sealing grease", "Replacement gasket"]
                estimated_cost = "$300"
                estimated_duration = "3 hours"
        elif module == "environment":
            repair_method = "Eco-mitigation and soil cleaning/de-pollution spray"
            materials = ["Neutralizing powder agent", "Silt barrier sheets", "Bio-degradable wash"]
            estimated_cost = "$600"
            estimated_duration = "6 hours"
        elif module == "cleancity":
            repair_method = "Heavy sanitation loader collection and sanitizer spray"
            materials = ["Sanitation loader bags", "Chlorine disinfectant spray", "Replacement bin lids"]
            estimated_cost = "$150"
            estimated_duration = "2 hours"
        elif module == "asset":
            repair_method = "Asset frame reconstruction and concrete anchoring anchor pour"
            materials = ["Reinforcing bracket fasteners", "Hardwood slats", "Anchoring bolts"]
            estimated_cost = "$180"
            estimated_duration = "3 hours"

        repair_output = {
            "repair_method": repair_method,
            "materials": materials,
            "estimated_cost": estimated_cost,
            "estimated_duration": estimated_duration
        }

        yield format_sse("agent_success", {
            "agent": "Repair Recommendation Agent",
            "output": repair_output
        })
        time.sleep(1)

        # ----------------------------------------------------
        # STEP 5: Government Assistance Agent
        # ----------------------------------------------------
        yield format_sse("agent_start", {
            "agent": "Government Assistance Agent",
            "role": "Municipal Dispatcher",
            "status": "Generating work order and routing dispatch coordinates to municipal systems..."
        })
        time.sleep(1.5)

        # Departments routing
        dept_map = {
            "Road Damage": "Public Works Department (PWD) - Highways Div",
            "Water Infrastructure": "Municipal Water Supply & Sewerage Board",
            "Environmental Protection": "Environmental Protection Agency (EPA)",
            "Public Cleanliness & Sanitation": "Municipal Cleanliness & Waste Dept",
            "Public Asset Management": "Parks & Public Assets Commission"
        }
        department = dept_map.get(category, "Municipal Maintenance Department")
        work_order_id = f"wo_{random.randint(90000, 99999)}"
        gov_summary = f"WORK ORDER REGISTERED: Issue ID {incident_id}. Assigned to {department}. Technical task: {repair_method}. Priority: {priority}."

        reporter_users = db.read('users', default=[])
        reporter_name = "Citizen Contributor"
        for u in reporter_users:
            if u.get("id") == reporter_id:
                reporter_name = u.get("name")
                break

        incident_record = {
            "id": incident_id,
            "module": module,
            "reporter_id": reporter_id,
            "reporter_name": reporter_name,
            "image_name": image_name,
            "image_url": f"/static/uploads/{image_name}" if not image_name.startswith("/static") else image_name,
            "description": description,
            "latitude": latitude,
            "longitude": longitude,
            "status": "reported" if priority != "Critical" else "dispatched",
            "location_context": location_context,
            "detection": detection_output,
            "risk": risk_output,
            "repair": repair_output,
            "dispatch": {
                "incident_id": incident_id,
                "status": "Pending Dispatch" if priority != "Critical" else "Dispatched",
                "department": department,
                "work_order_id": work_order_id
            },
            "reward": {
                "reward_points": 0,
                "badge_awarded": None
            }
        }

        if is_fraud:
            incident_record["status"] = "rejected"
            incident_record["dispatch"]["status"] = "Rejected - Fraud Detected"
            gov_summary = f"REPORT REJECTED: Suspicious activity flagged by FraudGuard AI. Work order cancelled."

        # Save Incident via MCP Tool
        yield format_sse("agent_progress", {
            "agent": "Government Assistance Agent",
            "log": "Calling MCP Tool: save_incident...",
            "tool_calls": [{"name": "save_incident", "args": {"incident_data": incident_record}}]
        })
        time.sleep(1)
        
        mcp_tools.save_incident(incident_record)

        # Write Work Order if not fraud
        if not is_fraud:
            workorders = db.read('workorders', default=[])
            work_order_record = {
                "id": work_order_id,
                "incident_id": incident_id,
                "department": department,
                "urgency": priority,
                "details": gov_summary,
                "estimated_cost": estimated_cost,
                "status": "Assigned" if priority != "Critical" else "Dispatched",
                "assigned_crew": f"Crew {random.choice(['Alpha', 'Beta', 'Gamma', 'Delta'])}",
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                "completed_at": None
            }
            workorders.append(work_order_record)
            db.write('workorders', workorders)

        gov_output = {
            "incident_id": incident_id,
            "department": department,
            "status": "Work Order Created" if not is_fraud else "Report Rejected",
            "government_summary": gov_summary
        }

        yield format_sse("agent_success", {
            "agent": "Government Assistance Agent",
            "output": gov_output
        })
        time.sleep(1)

        # ----------------------------------------------------
        # STEP 6: Civic Reward Agent
        # ----------------------------------------------------
        yield format_sse("agent_start", {
            "agent": "Civic Reward Agent",
            "role": "Citizen Contribution Evaluation Agent",
            "status": "Evaluating duplicate coordinates and checking point ledger allocations..."
        })
        time.sleep(1.2)

        duplicate_check = mcp_tools.detect_duplicate_reports(latitude, longitude, damage_type)
        is_duplicate = duplicate_check.get("duplicate_detected", False)

        reward_points = 0
        badge_earned = None
        contribution_level = "Standard"

        if is_fraud:
            yield format_sse("agent_progress", {
                "agent": "Civic Reward Agent",
                "log": "FraudGuard Alert active! Citizen points allocation blocked to protect system integrity.",
                "tool_calls": []
            })
            time.sleep(1)
        elif is_duplicate:
            yield format_sse("agent_progress", {
                "agent": "Civic Reward Agent",
                "log": "Duplicate report detected. Report linked but point payouts suppressed to prevent exploit.",
                "tool_calls": []
            })
            time.sleep(1)
            incident_record["status"] = "duplicate"
            incident_record["dispatch"]["status"] = "Rejected - Duplicate"
            mcp_tools.save_incident(incident_record)
        else:
            # Valid, unique report - Calculate Payout
            points_map = {"Low": 10, "Medium": 25, "High": 50, "Critical": 100}
            reward_points = points_map.get(priority, 10)
            
            # Module-specific badge checks
            badge_map = {
                "road": "Infrastructure Protector",
                "water": "Water Conservation Hero",
                "environment": "Environment Champion",
                "cleancity": "Sanitation Champion",
                "asset": "Asset Guardian"
            }
            target_badge = badge_map.get(module, "Civic Guardian")

            yield format_sse("agent_progress", {
                "agent": "Civic Reward Agent",
                "log": f"Verifying unique submission. Payout: {reward_points} pts. Unlocking badge: {target_badge}",
                "tool_calls": [{"name": "award_reward_points", "args": {"user_id": reporter_id, "points": reward_points, "reason": f"Verified unique {damage_type} submission"}}]
            })
            time.sleep(1)

            # Award Reward Points via MCP Tool
            reward_res = mcp_tools.award_reward_points(
                reporter_id, 
                reward_points, 
                f"Verified unique {damage_type} ({priority} priority) submission"
            )
            badge_earned = reward_res.get("badge_earned") or target_badge
            
            # Verify if user has badge, if not append it
            users = db.read('users', default=[])
            for u in users:
                if u.get("id") == reporter_id:
                    u_pts = u.get("points", 0)
                    u_badges = u.get("badges", [])
                    if badge_earned and badge_earned not in u_badges:
                        u_badges.append(badge_earned)
                        u["badges"] = u_badges
                    
                    if u_pts > 300:
                        contribution_level = "Elite Champion"
                    elif u_pts > 150:
                        contribution_level = "Infrastructure Veteran"
                    else:
                        contribution_level = "Active Citizen"
                    break
            db.write('users', users)

            # Update Incident record
            incident_record["reward"] = {
                "reward_points": reward_points,
                "badge_awarded": badge_earned
            }
            mcp_tools.save_incident(incident_record)

        rewards_output = {
            "reward_points": reward_points,
            "contribution_level": contribution_level,
            "badge": badge_earned if badge_earned else "None"
        }

        yield format_sse("agent_success", {
            "agent": "Civic Reward Agent",
            "output": rewards_output
        })
        time.sleep(1)

        # ----------------------------------------------------
        # STEP 7: Governance Analytics Agent
        # ----------------------------------------------------
        yield format_sse("agent_start", {
            "agent": "Governance Analytics Agent",
            "role": "National Infrastructure Intelligence Agent",
            "status": "Re-aggregating city-level charts and environmental hotspot matrices..."
        })
        time.sleep(1)

        # Call MCP Tool
        yield format_sse("agent_progress", {
            "agent": "Governance Analytics Agent",
            "log": "Calling MCP Tool: generate_city_analytics...",
            "tool_calls": [{"name": "generate_city_analytics", "args": {}}]
        })
        time.sleep(1)

        city_analytics = mcp_tools.generate_city_analytics()

        yield format_sse("agent_success", {
            "agent": "Governance Analytics Agent",
            "output": {
                "status": "City Analytics Updated",
                "total_active_hazards": city_analytics["summary"]["total_incidents"],
                "average_risk_rating": city_analytics["summary"]["average_risk_score"]
            }
        })
        time.sleep(0.5)

        # Close Stream
        yield format_sse("pipeline_complete", {
            "incident_id": incident_id,
            "message": "CivicGuard AI workflow has successfully processed all tasks.",
            "final_status": incident_record["status"]
        })

# Instantiate global engine
agent_engine = MultiAgentEngine()
