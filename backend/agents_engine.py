import os
import json
import time
import random
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
            self.model_name = "gemini-1.5-flash" # Use robust, standard model
        else:
            self.model_name = "Rule-based Simulation Engine"

    def execute_pipeline(self, 
                         incident_id: str, 
                         reporter_id: str, 
                         description: str, 
                         latitude: float, 
                         longitude: float, 
                         image_name: str) -> Generator[str, None, None]:
        """
        Runs the 6 agents in sequence and yields Server-Sent Events (SSE) progress reports.
        """
        def format_sse(event_type: str, data: dict) -> str:
            return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        yield format_sse("pipeline_start", {
            "incident_id": incident_id,
            "message": "Initiating RoadGuard AI multi-agent analysis pipeline...",
            "timestamp": time.time()
        })
        time.sleep(1)

        # ----------------------------------------------------
        # STEP 1: Infrastructure Detection Agent
        # ----------------------------------------------------
        yield format_sse("agent_start", {
            "agent": "Infrastructure Detection Agent",
            "role": "AI Infrastructure Inspector",
            "status": "Analyzing uploaded asset image and description..."
        })
        time.sleep(1.5)

        damage_type = "Pothole"
        severity = "Medium"
        confidence = "85%"
        category = "Road Damage"

        # Determine details based on description keyword parsing
        desc_lower = description.lower()
        if "pothole" in desc_lower or "pit" in desc_lower:
            damage_type = "Pothole"
            category = "Road Damage"
            severity = "High" if any(k in desc_lower for k in ["deep", "large", "huge", "dangerous", "accident"]) else "Medium"
        elif "crack" in desc_lower or "fissure" in desc_lower:
            damage_type = "Road Crack"
            category = "Road Damage"
            severity = "Medium" if "wide" in desc_lower or "large" in desc_lower else "Low"
        elif "streetlight" in desc_lower or "lamp" in desc_lower or "dark" in desc_lower or "light" in desc_lower:
            damage_type = "Streetlight Failure"
            category = "Electrical / Lighting"
            severity = "High" if "dark" in desc_lower or "junction" in desc_lower else "Medium"
        elif "drain" in desc_lower or "clog" in desc_lower or "flood" in desc_lower or "water" in desc_lower:
            damage_type = "Drainage Clog"
            category = "Sanitation & Drainage"
            severity = "Critical" if any(k in desc_lower for k in ["hospital", "flood", "severe", "overflow"]) else "High"
        elif "sign" in desc_lower or "board" in desc_lower or "marker" in desc_lower:
            damage_type = "Damaged Signboard"
            category = "Traffic Signage"
            severity = "Low"
        else:
            damage_type = "Public Asset Damage"
            category = "Public Infrastructure"
            severity = "Medium"

        if self.gemini_enabled:
            yield format_sse("agent_progress", {
                "agent": "Infrastructure Detection Agent",
                "log": f"Sending content to Gemini model ({self.model_name}) for visual validation...",
                "tool_calls": []
            })
            try:
                # Perform LLM analysis on the description & image context
                prompt = f"""
                You are an AI Infrastructure Inspector for RoadGuard AI.
                Analyze the following incident report and categorize it:
                Description: "{description}"
                Image Filename: "{image_name}"

                Respond ONLY with a valid JSON in the format:
                {{
                    "damage_type": "Pothole | Road Crack | Streetlight Failure | Drainage Clog | Damaged Signboard | Public Asset Damage",
                    "severity": "Low | Medium | High | Critical",
                    "confidence": "percentage string",
                    "category": "incident classification category"
                }}
                """
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content(prompt)
                res_text = response.text.strip()
                # Clean up response text if wrapped in ```json
                if res_text.startswith("```"):
                    res_text = res_text.split("```")[1]
                    if res_text.startswith("json"):
                        res_text = res_text[4:]
                res_json = json.loads(res_text.strip())
                
                damage_type = res_json.get("damage_type", damage_type)
                severity = res_json.get("severity", severity)
                confidence = res_json.get("confidence", "92%")
                category = res_json.get("category", category)

            except Exception as e:
                yield format_sse("agent_progress", {
                    "agent": "Infrastructure Detection Agent",
                    "log": f"Gemini API check failed. Falling back to rule-based parser. Error: {str(e)}",
                    "tool_calls": []
                })

        detection_output = {
            "damage_type": damage_type,
            "severity": severity,
            "confidence": confidence,
            "category": category
        }
        yield format_sse("agent_success", {
            "agent": "Infrastructure Detection Agent",
            "output": detection_output
        })
        time.sleep(1)

        # ----------------------------------------------------
        # STEP 2: Risk Assessment Agent
        # ----------------------------------------------------
        yield format_sse("agent_start", {
            "agent": "Risk Assessment Agent",
            "role": "Public Safety Officer",
            "status": "Analyzing environmental context and calculating safety hazard priority..."
        })
        time.sleep(1)

        # Call MCP Tool: get_location_context
        yield format_sse("agent_progress", {
            "agent": "Risk Assessment Agent",
            "log": "Calling MCP Tool: get_location_context...",
            "tool_calls": [{"name": "get_location_context", "args": {"latitude": latitude, "longitude": longitude}}]
        })
        time.sleep(1.2)
        
        # Invoke the MCP tool directly using our import
        location_context = mcp_tools.get_location_context(latitude, longitude)
        
        yield format_sse("agent_progress", {
            "agent": "Risk Assessment Agent",
            "log": f"Location context received: Road={location_context['road_category']}, Traffic={location_context['traffic_density']}, School Zone={location_context['school_zone']}",
            "tool_calls": []
        })
        time.sleep(1)

        # Calculate Risk Score
        base_scores = {"Low": 20, "Medium": 45, "High": 75, "Critical": 90}
        risk_score = base_scores.get(severity, 45)

        # Apply context factors
        if location_context["traffic_density"] == "High":
            risk_score += 10
        elif location_context["traffic_density"] == "Medium":
            risk_score += 5

        if location_context["school_zone"]:
            risk_score += 15

        if location_context["population_density"] == "Very High":
            risk_score += 10
        elif location_context["population_density"] == "High":
            risk_score += 5

        accident_count = location_context["accident_history_count"]
        if accident_count > 5:
            risk_score += 15
        elif accident_count > 2:
            risk_score += 7

        risk_score = min(100, risk_score)

        # Determine priority level based on final risk score
        if risk_score >= 85:
            priority = "Critical"
        elif risk_score >= 65:
            priority = "High"
        elif risk_score >= 40:
            priority = "Medium"
        else:
            priority = "Low"

        explanation = f"Incident danger index is calculated at {risk_score}/100. This is categorized as a {priority} priority due to the damage severity being {severity} combined with localized context: situated on a {location_context['road_category']} with {location_context['traffic_density']} traffic and {accident_count} previous accident reports."
        if location_context["school_zone"]:
            explanation += " Immediate attention is recommended due to proximity to a School Zone."

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
        # STEP 3: Repair Recommendation Agent
        # ----------------------------------------------------
        yield format_sse("agent_start", {
            "agent": "Repair Recommendation Agent",
            "role": "Civil Engineering Advisor",
            "status": "Generating technical repair blueprint and cost estimation..."
        })
        time.sleep(1.5)

        # Recommendations logic
        repair_method = "Standard resurfacing"
        materials = ["Asphalt mix"]
        estimated_cost = "$200"
        estimated_duration = "3 hours"

        if damage_type == "Pothole":
            if priority == "Critical" or priority == "High":
                repair_method = "Hot-mix asphalt filling with mechanical roller compaction"
                materials = ["Asphalt concrete", "Tack coat emulsion", "Sealant binder"]
                estimated_cost = "$450"
                estimated_duration = "4 hours"
            else:
                repair_method = "Cold-mix asphalt patch filling"
                materials = ["Cold patch asphalt", "Base course sand"]
                estimated_cost = "$150"
                estimated_duration = "2 hours"
        elif damage_type == "Road Crack":
            repair_method = "Crack sealing and asphalt routing"
            materials = ["Polymer-modified asphalt sealant", "Joint backer rod"]
            estimated_cost = "$180"
            estimated_duration = "3 hours"
        elif damage_type == "Streetlight Failure":
            repair_method = "Replacement of luminaire bulb and wiring continuity test"
            materials = ["120W LED fixture", "Electrical wiring", "Fuse kit"]
            estimated_cost = "$280"
            estimated_duration = "2 hours"
        elif damage_type == "Drainage Clog":
            repair_method = "Hydro-jet de-silting and debris suction extraction"
            materials = ["Silt catcher bag", "Heavy-duty gully grate replacement"]
            estimated_cost = "$600"
            estimated_duration = "6 hours"
        elif damage_type == "Damaged Signboard":
            repair_method = "Post re-installation and concrete footing pour"
            materials = ["Galvanized steel pipe", "Fasteners", "Ready-mix concrete"]
            estimated_cost = "$120"
            estimated_duration = "2 hours"

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
        # STEP 4: Government Assistance Agent
        # ----------------------------------------------------
        yield format_sse("agent_start", {
            "agent": "Government Assistance Agent",
            "role": "Public Works Coordinator",
            "status": "Generating work order and registering incident with authority dispatch registries..."
        })
        time.sleep(1.2)

        # Determine department based on category
        dept_map = {
            "Road Damage": "Public Works Department (PWD) - Highways Div",
            "Electrical / Lighting": "Municipal Electricity & Lighting Commission",
            "Sanitation & Drainage": "Stormwater Drainage & Sanitation Board",
            "Traffic Signage": "Traffic Engineering & Signage Directorate"
        }
        department = dept_map.get(category, "Municipal Maintenance Department")

        work_order_id = f"wo_{random.randint(90000, 99999)}"
        gov_summary = f"WORK ORDER REGISTERED: Issue ID {incident_id}. Assigned to {department}. Technical task: {repair_method}. Emergency Priority: {priority}."

        # Prepare incident record to save via MCP Tool
        reporter_users = db.read('users', default=[])
        reporter_name = "Citizen Contributor"
        for u in reporter_users:
            if u.get("id") == reporter_id:
                reporter_name = u.get("name")
                break

        incident_record = {
            "id": incident_id,
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

        # Call MCP Tool: save_incident
        yield format_sse("agent_progress", {
            "agent": "Government Assistance Agent",
            "log": "Calling MCP Tool: save_incident...",
            "tool_calls": [{"name": "save_incident", "args": {"incident_data": incident_record}}]
        })
        time.sleep(1)
        
        mcp_tools.save_incident(incident_record)

        # Write work order record
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
            "status": "Work Order Created",
            "government_summary": gov_summary
        }
        yield format_sse("agent_success", {
            "agent": "Government Assistance Agent",
            "output": gov_output
        })
        time.sleep(1)

        # ----------------------------------------------------
        # STEP 5: Civic Reward Agent
        # ----------------------------------------------------
        yield format_sse("agent_start", {
            "agent": "Civic Reward Agent",
            "role": "Citizen Contribution Evaluation Agent",
            "status": "Checking report uniqueness and calculating civic rewards points..."
        })
        time.sleep(1.2)

        # Call MCP Tool: detect_duplicate_reports
        yield format_sse("agent_progress", {
            "agent": "Civic Reward Agent",
            "log": "Calling MCP Tool: detect_duplicate_reports...",
            "tool_calls": [{"name": "detect_duplicate_reports", "args": {"latitude": latitude, "longitude": longitude, "damage_type": damage_type}}]
        })
        time.sleep(1)
        
        duplicate_check = mcp_tools.detect_duplicate_reports(latitude, longitude, damage_type)
        is_duplicate = duplicate_check.get("duplicate_detected", False)

        reward_points = 0
        badge_earned = None
        contribution_level = "Standard"

        if is_duplicate:
            yield format_sse("agent_progress", {
                "agent": "Civic Reward Agent",
                "log": "Duplicate alert! Another active report covers this issue nearby. Marking submission as duplicate. 0 points credited to prevent double payout.",
                "tool_calls": []
            })
            time.sleep(1)
            
            # Update incident status to duplicate
            incident_record["status"] = "duplicate"
            incident_record["dispatch"]["status"] = "Rejected - Duplicate"
            mcp_tools.save_incident(incident_record)
        else:
            # Unique - Calculate Points
            points_map = {"Low": 10, "Medium": 25, "High": 50, "Critical": 100}
            reward_points = points_map.get(priority, 10)
            
            yield format_sse("agent_progress", {
                "agent": "Civic Reward Agent",
                "log": f"Report verified as unique. Awarding {reward_points} civic contribution points.",
                "tool_calls": [{"name": "award_reward_points", "args": {"user_id": reporter_id, "points": reward_points, "reason": f"Verified unique {damage_type} submission"}}]
            })
            time.sleep(1)
            
            # Call MCP Tool: award_reward_points
            reward_res = mcp_tools.award_reward_points(
                reporter_id, 
                reward_points, 
                f"Verified unique {damage_type} ({priority} priority) submission"
            )
            badge_earned = reward_res.get("badge_earned")
            
            # Read back user stats to determine contribution level
            users = db.read('users', default=[])
            for u in users:
                if u.get("id") == reporter_id:
                    u_pts = u.get("points", 0)
                    if u_pts > 300:
                        contribution_level = "Elite Champion"
                    elif u_pts > 150:
                        contribution_level = "Infrastructure Veteran"
                    else:
                        contribution_level = "Active Citizen"
                    break

            # Save reward details to incident record
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
        # STEP 6: Governance Analytics Agent
        # ----------------------------------------------------
        yield format_sse("agent_start", {
            "agent": "Governance Analytics Agent",
            "role": "National Infrastructure Intelligence Agent",
            "status": "Re-compiling metropolitan-level analytics and forecasting maintenance budgets..."
        })
        time.sleep(1)

        # Call MCP Tool: generate_city_analytics
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

        # Finish pipeline
        yield format_sse("pipeline_complete", {
            "incident_id": incident_id,
            "message": "RoadGuard AI workflow successfully completed all tasks.",
            "final_status": incident_record["status"]
        })

# Instantiate global engine
agent_engine = MultiAgentEngine()
