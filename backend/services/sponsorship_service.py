"""
Sponsorship Management Service
Handles sponsor profiles, packages, contract statuses, deliverable tracking, and engagement metrics.
"""

import uuid
from datetime import datetime
from backend.models import get_db

def get_all_sponsors(tier_filter=None, status_filter=None, search=None):
    with get_db() as conn:
        query = "SELECT * FROM sponsors WHERE 1=1"
        params = []
        if tier_filter and tier_filter != "All":
            query += " AND tier = ?"
            params.append(tier_filter)
        if status_filter and status_filter != "All":
            query += " AND contract_status = ?"
            params.append(status_filter)
        if search:
            query += " AND (name LIKE ? OR contact_person LIKE ?)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")
        query += " ORDER BY name ASC"

        sponsors = conn.execute(query, params).fetchall()
        result = []
        for s in sponsors:
            spn = dict(s)
            delivs = conn.execute("SELECT * FROM sponsorship_deliverables WHERE sponsor_id = ?", (spn["id"],)).fetchall()
            deliv_list = [dict(d) for d in delivs]
            completed = sum(1 for d in deliv_list if d["status"] == "Completed")
            total = len(deliv_list)
            spn["deliverables_summary"] = {
                "completed": completed,
                "total": total,
                "percentage": int((completed / total * 100)) if total > 0 else 0
            }
            result.append(spn)
        return result

def get_sponsor_details(sponsor_id):
    with get_db() as conn:
        spn = conn.execute("SELECT * FROM sponsors WHERE id = ?", (sponsor_id,)).fetchone()
        if not spn:
            return None
        result = dict(spn)
        delivs = conn.execute("SELECT * FROM sponsorship_deliverables WHERE sponsor_id = ? ORDER BY due_date ASC", (sponsor_id,)).fetchall()
        result["deliverables"] = [dict(d) for d in delivs]
        eng = conn.execute("SELECT * FROM sponsor_engagements WHERE sponsor_id = ?", (sponsor_id,)).fetchone()
        result["engagement"] = dict(eng) if eng else {
            "booth_visits": 0, "attendee_interactions": 0, "session_participation": 0,
            "social_engagement": 0, "engagement_score": result.get("engagement_score", 0)
        }
        return result

def create_sponsor(data):
    sponsor_id = f"SPN-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO sponsors (id, event_id, name, tier, contact_person, contact_email, phone,
                contract_status, contract_value, payment_status, total_amount, paid_amount, engagement_score, overall_performance, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sponsor_id,
            data.get("event_id", "EVT-1001"),
            data.get("name"),
            data.get("tier", "Gold"),
            data.get("contact_person", ""),
            data.get("contact_email", ""),
            data.get("phone", ""),
            data.get("contract_status", "Signed"),
            data.get("contract_value", 5000.0),
            data.get("payment_status", "Pending"),
            data.get("total_amount", 5000.0),
            data.get("paid_amount", 0.0),
            data.get("engagement_score", 75),
            data.get("overall_performance", "Good"),
            now
        ))
        
        # Create default deliverables based on tier
        tier = data.get("tier", "Gold")
        default_delivs = []
        if tier == "Platinum":
            default_delivs = [
                ("Main-Stage Branding", "Logo placement on central stage screens", "Completed"),
                ("Promotional Session 1", "30-min keynote speaking slot", "Completed"),
                ("Promotional Session 2", "15-min product spotlight session", "Pending"),
                ("Exhibition Booth #101", "Prime booth location at main hall entrance", "Completed"),
                ("Social Media Promotion", "Dedicated posts across official channels", "Overdue"),
                ("Complimentary Passes (10)", "10 VIP all-access passes delivered", "Completed")
            ]
        elif tier == "Gold":
            default_delivs = [
                ("Keynote Stage Logo", "Logo on sponsor slide", "Completed"),
                ("Exhibition Booth #202", "Standard booth in hall A", "Completed"),
                ("Social Media Mention", "Combined post with Gold sponsors", "Pending"),
                ("Complimentary Passes (5)", "5 General access passes", "Completed")
            ]
        else:
            default_delivs = [
                ("Website Logo Display", "Logo on official event site", "Completed"),
                ("Complimentary Passes (2)", "2 General access passes", "Completed")
            ]

        for d_name, d_desc, d_status in default_delivs:
            conn.execute("""
                INSERT INTO sponsorship_deliverables (id, sponsor_id, deliverable_name, description, status, completion_percentage)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f"DEL-{uuid.uuid4().hex[:6].upper()}", sponsor_id, d_name, d_desc, d_status, 100 if d_status=="Completed" else 0))

        # Create initial engagement record
        conn.execute("""
            INSERT INTO sponsor_engagements (id, sponsor_id, booth_visits, attendee_interactions, session_participation, social_engagement, engagement_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (f"ENG-{uuid.uuid4().hex[:6].upper()}", sponsor_id, 120, 340, 2, 450, data.get("engagement_score", 75)))

    return get_sponsor_details(sponsor_id)

def update_deliverable(deliverable_id, status):
    now = datetime.utcnow().isoformat() if status == "Completed" else None
    pct = 100 if status == "Completed" else (50 if status == "In Progress" else 0)
    with get_db() as conn:
        conn.execute("""
            UPDATE sponsorship_deliverables
            SET status = ?, completion_percentage = ?, completed_at = ?
            WHERE id = ?
        """, (status, pct, now, deliverable_id))
    return True

def calculate_sponsor_performance(engagement_pct, leads, deliverables_pct):
    """
    Dynamically computes performance score and category from underlying data:
    - Engagement % (40% weight)
    - Deliverables completion % (35% weight)
    - Lead count benchmarked to 450 leads (25% weight)
    """
    lead_score = min((float(leads) / 450.0) * 100.0, 100.0) if leads is not None else 0.0
    eng_score = float(engagement_pct) if engagement_pct is not None else 0.0
    deliv_score = float(deliverables_pct) if deliverables_pct is not None else 0.0

    total_score = round((eng_score * 0.40) + (deliv_score * 0.35) + (lead_score * 0.25), 1)

    if total_score >= 85:
        category = "Excellent"
    elif total_score >= 70:
        category = "Good"
    else:
        category = "At Risk"

    return total_score, category

def generate_sponsor_ai_insight(name, tier, eng_pct, leads, deliv_pct, category, score):
    """
    Generates a structured AI performance insight explaining:
    - Why the category was assigned
    - What is going well
    - What needs improvement
    - Recommended action
    """
    if category == "Excellent":
        explanation = f"{name} has outstanding engagement at {eng_pct}%, generated {leads} leads, and completed {deliv_pct}% of its deliverables."
        going_well = f"High brand visibility, exceptional lead acquisition ({leads} leads), and perfect deliverable execution."
        needs_improvement = "Maintain current momentum and consider upgrade to higher tier package for next event."
        recommendation = "Provide VIP sponsor executive lounge access and offer priority renewal terms for the upcoming event."
    elif category == "Good":
        explanation = f"{name} shows solid performance with {eng_pct}% engagement, {leads} leads generated, and {deliv_pct}% deliverable completion."
        going_well = "Consistent booth traffic and good attendee interaction across main sessions."
        needs_improvement = f"Lead count ({leads}) is slightly below top-tier benchmarks; {100 - deliv_pct}% of promotional deliverables remain pending."
        recommendation = "Assist sponsor team with attendee badge scanning at keynote hall entrances to boost captured leads."
    else: # At Risk
        explanation = f"{name} has low engagement at {eng_pct}%, generated only {leads} leads, and has completed {deliv_pct}% of its deliverables. The sponsor is at risk of under-delivering ROI."
        going_well = "Official presence established with initial attendee interactions."
        needs_improvement = f"Critical deficit in attendee engagement ({eng_pct}%) and lead generation ({leads} leads). Overdue promotional deliverables need immediate dispatch."
        recommendation = "Schedule an urgent operational check-in, issue push notification reminders for booth drop-ins, and assign a dedicated sponsor liaison."

    return {
        "summary": f"{name} – {category}",
        "explanation": explanation,
        "going_well": going_well,
        "needs_improvement": needs_improvement,
        "recommendation": recommendation
    }

def get_sponsor_performance():
    with get_db() as conn:
        sponsors = conn.execute("SELECT * FROM sponsors ORDER BY name ASC").fetchall()
        result = []
        total_eng = 0
        total_leads = 0
        total_deliv_pct = 0

        for s in sponsors:
            spn = dict(s)
            delivs = conn.execute("SELECT * FROM sponsorship_deliverables WHERE sponsor_id = ?", (spn["id"],)).fetchall()
            deliv_list = [dict(d) for d in delivs]
            
            total_delivs = len(deliv_list)
            completed_delivs = sum(1 for d in deliv_list if d["status"] == "Completed")
            
            if total_delivs > 0:
                sum_pct = sum(d.get("completion_percentage", 0) for d in deliv_list)
                deliv_pct = int(sum_pct / total_delivs)
            else:
                deliv_pct = 0

            eng = conn.execute("SELECT * FROM sponsor_engagements WHERE sponsor_id = ?", (spn["id"],)).fetchone()
            eng_dict = dict(eng) if eng else {
                "booth_visits": 0, "attendee_interactions": 0, "session_participation": 0,
                "social_engagement": 0, "leads": 0, "engagement_score": spn.get("engagement_score", 75)
            }
            
            eng_pct = eng_dict.get("engagement_score", 75)
            leads = eng_dict.get("leads", 0)

            total_eng += eng_pct
            total_leads += leads
            total_deliv_pct += deliv_pct

            # Calculate score and category dynamically
            score, category = calculate_sponsor_performance(eng_pct, leads, deliv_pct)
            
            # Generate AI insight
            ai_insight = generate_sponsor_ai_insight(spn["name"], spn["tier"], eng_pct, leads, deliv_pct, category, score)

            result.append({
                "id": spn["id"],
                "name": spn["name"],
                "tier": spn["tier"],
                "engagement_pct": eng_pct,
                "leads": leads,
                "deliverables_pct": deliv_pct,
                "deliverables_summary": {
                    "completed": completed_delivs,
                    "total": total_delivs
                },
                "performance_score": score,
                "performance_category": category,
                "ai_insight": ai_insight,
                "engagements": eng_dict,
                "deliverables": deliv_list
            })

        count = len(result)
        summary = {
            "total_sponsors": count,
            "avg_engagement_pct": round(total_eng / count, 1) if count > 0 else 0,
            "total_leads_generated": total_leads,
            "avg_deliverables_pct": round(total_deliv_pct / count, 1) if count > 0 else 0
        }

        return {"sponsors": result, "summary": summary}

def get_sponsor_performance_detail(sponsor_id):
    with get_db() as conn:
        spn = conn.execute("SELECT * FROM sponsors WHERE id = ?", (sponsor_id,)).fetchone()
        if not spn:
            return None
        spn_dict = dict(spn)
        
        delivs = conn.execute("SELECT * FROM sponsorship_deliverables WHERE sponsor_id = ? ORDER BY deliverable_name ASC", (sponsor_id,)).fetchall()
        deliv_list = [dict(d) for d in delivs]
        
        total_delivs = len(deliv_list)
        completed_delivs = sum(1 for d in deliv_list if d["status"] == "Completed")
        deliv_pct = int(sum(d.get("completion_percentage", 0) for d in deliv_list) / total_delivs) if total_delivs > 0 else 0
        
        eng = conn.execute("SELECT * FROM sponsor_engagements WHERE sponsor_id = ?", (sponsor_id,)).fetchone()
        eng_dict = dict(eng) if eng else {"booth_visits": 0, "attendee_interactions": 0, "session_participation": 0, "social_engagement": 0, "leads": 0, "engagement_score": 75}
        
        eng_pct = eng_dict.get("engagement_score", 75)
        leads = eng_dict.get("leads", 0)
        
        score, category = calculate_sponsor_performance(eng_pct, leads, deliv_pct)
        ai_insight = generate_sponsor_ai_insight(spn_dict["name"], spn_dict["tier"], eng_pct, leads, deliv_pct, category, score)
        
        return {
            "id": spn_dict["id"],
            "name": spn_dict["name"],
            "tier": spn_dict["tier"],
            "engagement_pct": eng_pct,
            "leads": leads,
            "deliverables_pct": deliv_pct,
            "performance_score": score,
            "performance_category": category,
            "ai_insight": ai_insight,
            "engagements": eng_dict,
            "deliverables": deliv_list
        }

def update_sponsor_metrics(sponsor_id, leads=None, engagement_score=None):
    with get_db() as conn:
        eng = conn.execute("SELECT * FROM sponsor_engagements WHERE sponsor_id = ?", (sponsor_id,)).fetchone()
        if eng:
            new_leads = leads if leads is not None else eng["leads"]
            new_eng = engagement_score if engagement_score is not None else eng["engagement_score"]
            conn.execute("""
                UPDATE sponsor_engagements
                SET leads = ?, engagement_score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE sponsor_id = ?
            """, (new_leads, new_eng, sponsor_id))
            conn.execute("UPDATE sponsors SET engagement_score = ? WHERE id = ?", (new_eng, sponsor_id))
    return get_sponsor_performance_detail(sponsor_id)

def get_prospects(domain=None):
    with get_db() as conn:
        q = "SELECT * FROM sponsor_prospects"
        params = []
        if domain and domain != "All":
            q += " WHERE domain = ?"
            params.append(domain)
        q += " ORDER BY estimated_budget DESC"
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]

def approach_prospect(prospect_id, payload):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM sponsor_prospects WHERE id = ?", (prospect_id,)).fetchone()
        if not row:
            return None
        prospect = dict(row)
        
        # update status
        conn.execute("UPDATE sponsor_prospects SET status = 'Contacted' WHERE id = ?", (prospect_id,))
        conn.commit()
    
    # Save proposal to outbox directory
    import os
    import time
    from backend.config import OUTBOX_DIR
    
    body = f"""
    <h3>Partnership Opportunity for {prospect['name']}</h3>
    <p>{payload.get('message', 'We would like to invite you to sponsor our event.')}</p>
    <ul>
      <li>Requested Tier: {payload.get('tier', 'Gold')}</li>
      <li>Target Budget: ${payload.get('amount', prospect['estimated_budget'])}</li>
    </ul>
    <p>Please reach out to discuss further.</p>
    """
    
    filename = f"proposal_{prospect_id}_{int(time.time())}.html"
    filepath = os.path.join(OUTBOX_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(body)
        
    return prospect
