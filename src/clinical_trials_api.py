"""ClinicalTrials.gov API functions"""

import requests

CT_API_BASE = "https://clinicaltrials.gov/api/v2/studies"


def count_trials(condition=None, phase=None, status=None, location=None):
    """Count trials by fetching multiple pages - returns ONLY count, no trial data"""
    params = {
        "format": "json",
        "pageSize": 100
    }
    
    query_parts = []
    if condition:
        query_parts.append(f"AREA[Condition]{condition}")
    if phase:
        query_parts.append(f"AREA[Phase]{phase}")
    if status:
        query_parts.append(f"AREA[OverallStatus]{status}")
    if location:
        query_parts.append(f"AREA[LocationCountry]{location}")
    
    if query_parts:
        params["query.term"] = " AND ".join(query_parts)
    
    try:
        total_count = 0
        page_count = 0
        max_pages = 3
        next_token = None
        
        while page_count < max_pages:
            if next_token:
                params["pageToken"] = next_token
            
            response = requests.get(CT_API_BASE, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            studies = data.get("studies", [])
            total_count += len(studies)
            page_count += 1
            
            next_token = data.get("nextPageToken")
            if not next_token:
                return {"count": total_count, "is_exact": True}
        
        return {
            "count": total_count,
            "is_exact": False,
            "note": f"At least {total_count} trials"
        }
        
    except Exception as e:
        return {"error": str(e)}


def show_trials(nctId):
    """Show full trial details for a given NCT ID"""
    path = CT_API_BASE + "/" + nctId
    response = requests.get(path, timeout=30)
    data = response.json()
    return _parse_study(data, full_details=True)


def _parse_study(study, full_details=False):
    """Parse a study object into a compact/detailed format"""
    protocol = study.get("protocolSection", {})
    
    # Identification
    id_module = protocol.get("identificationModule", {})
    nct_id = id_module.get("nctId", "")
    title = id_module.get("briefTitle", "")
    official_title = id_module.get("officialTitle", "")
    acronym = id_module.get("acronym", "")
    organization = id_module.get("organization", {}).get("fullName", "")
    
    # Status & Dates
    status_module = protocol.get("statusModule", {})
    overall_status = status_module.get("overallStatus", "")
    start_date = status_module.get("startDateStruct", {}).get("date", "")
    start_date_type = status_module.get("startDateStruct", {}).get("type", "")
    completion_date = status_module.get("completionDateStruct", {}).get("date", "")
    completion_date_type = status_module.get("completionDateStruct", {}).get("type", "")
    primary_completion_date = status_module.get("primaryCompletionDateStruct", {}).get("date", "")
    first_posted = status_module.get("studyFirstPostDateStruct", {}).get("date", "")
    last_updated = status_module.get("lastUpdatePostDateStruct", {}).get("date", "")
    first_submit_date = status_module.get("studyFirstSubmitDate", "")
    
    # Sponsor
    sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
    lead_sponsor = sponsor_module.get("leadSponsor", {})
    sponsor_name = lead_sponsor.get("name", "")
    sponsor_class = lead_sponsor.get("class", "")
    responsible_party = sponsor_module.get("responsibleParty", {})
    investigator_name = responsible_party.get("investigatorFullName", "")
    investigator_affiliation = responsible_party.get("investigatorAffiliation", "")
    
    # Description
    description_module = protocol.get("descriptionModule", {})
    brief_summary = description_module.get("briefSummary", "")
    detailed_description = description_module.get("detailedDescription", "")
    
    # Conditions
    conditions_module = protocol.get("conditionsModule", {})
    conditions = conditions_module.get("conditions", [])
    
    # Design
    design_module = protocol.get("designModule", {})
    study_type = design_module.get("studyType", "")
    phases = design_module.get("phases", [])
    enrollment_info = design_module.get("enrollmentInfo", {})
    enrollment_count = enrollment_info.get("count", 0)
    enrollment_type = enrollment_info.get("type", "")
    design_info = design_module.get("designInfo", {})
    allocation = design_info.get("allocation", "")
    intervention_model = design_info.get("interventionModel", "")
    primary_purpose = design_info.get("primaryPurpose", "")
    
    # Interventions
    arms_module = protocol.get("armsInterventionsModule", {})
    interventions_raw = arms_module.get("interventions", [])
    interventions = []
    for interv in interventions_raw:
        interventions.append({
            "type": interv.get("type", ""),
            "name": interv.get("name", ""),
            "description": interv.get("description", "")[:200] if not full_details else interv.get("description", "")
        })
    
    # Eligibility
    eligibility_module = protocol.get("eligibilityModule", {})
    eligibility_criteria = eligibility_module.get("eligibilityCriteria", "")
    healthy_volunteers = eligibility_module.get("healthyVolunteers", False)
    sex = eligibility_module.get("sex", "")
    min_age = eligibility_module.get("minimumAge", "")
    max_age = eligibility_module.get("maximumAge", "")
    std_ages = eligibility_module.get("stdAges", [])
    
    # Locations
    contacts_module = protocol.get("contactsLocationsModule", {})
    locations_raw = contacts_module.get("locations", [])
    locations = []
    for loc in locations_raw[:10]:  # Limit to 10 locations
        locations.append({
            "facility": loc.get("facility", ""),
            "city": loc.get("city", ""),
            "state": loc.get("state", ""),
            "country": loc.get("country", ""),
            "status": loc.get("status", "")
        })
    
    # Outcomes (only for full details)
    outcomes_module = protocol.get("outcomesModule", {})
    primary_outcomes = []
    secondary_outcomes = []
    if full_details:
        for outcome in outcomes_module.get("primaryOutcomes", []):
            primary_outcomes.append({
                "measure": outcome.get("measure", ""),
                "description": outcome.get("description", ""),
                "timeFrame": outcome.get("timeFrame", "")
            })
        for outcome in outcomes_module.get("secondaryOutcomes", []):
            secondary_outcomes.append({
                "measure": outcome.get("measure", ""),
                "timeFrame": outcome.get("timeFrame", "")
            })
    
    # Build result
    result = {
        "nctId": nct_id,
        "title": title,
        "acronym": acronym,
        "status": overall_status,
        "phases": phases,
        "studyType": study_type,
        "conditions": conditions,
        "interventions": interventions,
        "sponsor": sponsor_name,
        "sponsorClass": sponsor_class,
        "enrollment": {"count": enrollment_count, "type": enrollment_type},
        "dates": {
            "start": start_date,
            "startType": start_date_type,
            "completion": completion_date,
            "completionType": completion_date_type,
            "primaryCompletion": primary_completion_date,
            "firstPosted": first_posted,
            "lastUpdated": last_updated,
            "firstSubmit": first_submit_date
        },
        "eligibility": {
            "criteria": eligibility_criteria[:800] if not full_details else eligibility_criteria,
            "sex": sex,
            "minAge": min_age,
            "maxAge": max_age,
            "stdAges": std_ages,
            "healthyVolunteers": healthy_volunteers
        },
        "locations": locations
    }
    
    # Add extra details for full view
    if full_details:
        result["officialTitle"] = official_title
        result["organization"] = organization
        result["investigator"] = investigator_name
        result["investigatorAffiliation"] = investigator_affiliation
        result["briefSummary"] = brief_summary
        result["detailedDescription"] = detailed_description
        result["design"] = {
            "allocation": allocation,
            "interventionModel": intervention_model,
            "primaryPurpose": primary_purpose
        }
        result["primaryOutcomes"] = primary_outcomes
        result["secondaryOutcomes"] = secondary_outcomes
    
    return result


def search_trials(condition=None, phase=None, status=None, location=None, 
                   sponsor=None, intervention=None, study_type=None,
                   start_date_from=None, start_date_to=None,
                   max_results=10):
    """Search ClinicalTrials.gov for trials matching criteria
    
    Args:
        condition: Medical condition (e.g., 'diabetes')
        phase: Trial phase (e.g., 'Phase 3')
        status: Trial status (e.g., 'Recruiting', 'Completed')
        location: Country or city name (e.g., 'France', 'Paris')
        sponsor: Lead sponsor name (e.g., 'Pfizer')
        intervention: Intervention/treatment name (e.g., 'insulin')
        study_type: Study type ('Interventional' or 'Observational')
        start_date_from: Start date range begin (YYYY-MM-DD)
        start_date_to: Start date range end (YYYY-MM-DD)
        max_results: Maximum results to return (default 10, max 20)
    """
    max_results = min(max_results, 20)
    
    params = {
        "format": "json",
        "pageSize": max_results
    }
    
    query_parts = []
    if condition:
        query_parts.append(f"AREA[Condition]{condition}")
    if phase:
        query_parts.append(f"AREA[Phase]{phase}")
    if status:
        query_parts.append(f"AREA[OverallStatus]{status}")
    if location:
        query_parts.append(f"AREA[LocationCountry]{location}")
    if sponsor:
        query_parts.append(f"AREA[LeadSponsorName]{sponsor}")
    if intervention:
        query_parts.append(f"AREA[InterventionName]{intervention}")
    if study_type:
        query_parts.append(f"AREA[StudyType]{study_type}")
    if start_date_from and start_date_to:
        query_parts.append(f"AREA[StartDate]RANGE[{start_date_from},{start_date_to}]")
    elif start_date_from:
        query_parts.append(f"AREA[StartDate]RANGE[{start_date_from},MAX]")
    elif start_date_to:
        query_parts.append(f"AREA[StartDate]RANGE[MIN,{start_date_to}]")
    
    if query_parts:
        params["query.term"] = " AND ".join(query_parts)
    
    try:
        response = requests.get(CT_API_BASE, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        full_studies = data.get("studies", [])
        
        return [_parse_study(study) for study in full_studies]
    
    except Exception as e:
        return {"error": str(e)}


def analyze_criteria(trials):
    """Extract and analyze eligibility criteria from trials"""
    if isinstance(trials, dict) and "error" in trials:
        return trials
    
    all_criteria = {
        "inclusion": [],
        "exclusion": []
    }
    
    for trial in trials:
        try:
            criteria_text = trial.get("eligibility", {}).get("criteria", "")
            
            if not criteria_text:
                continue
            
            if "Inclusion Criteria" in criteria_text:
                inclusion_text = criteria_text.split("Inclusion Criteria")[1]
                if "Exclusion Criteria" in inclusion_text:
                    inclusion_text = inclusion_text.split("Exclusion Criteria")[0]
                all_criteria["inclusion"].append(inclusion_text.strip())
            
            if "Exclusion Criteria" in criteria_text:
                exclusion_text = criteria_text.split("Exclusion Criteria")[1]
                all_criteria["exclusion"].append(exclusion_text.strip())
                
        except Exception:
            continue
    
    return all_criteria


def calculate_statistics(condition=None, phase=None, status=None, location=None, 
                          sponsor=None, max_results=20):
    """Calculate statistics by fetching trials and computing stats including duration"""
    from datetime import datetime
    
    # Fetch trials using the same logic as search_trials
    trials = search_trials(
        condition=condition,
        phase=phase,
        status=status,
        location=location,
        sponsor=sponsor,
        max_results=max_results
    )
    
    if isinstance(trials, dict) and "error" in trials:
        return trials
    
    stats = {
        "total_trials": len(trials),
        "trial_nct_ids": [t.get("nctId") for t in trials if t.get("nctId")],
        "phases": {},
        "statuses": {},
        "studyTypes": {},
        "sponsors": {},
        "enrollment": {"total": 0, "count": 0},
        "duration": {"total_days": 0, "count": 0, "durations": []}
    }
    
    for trial in trials:
        try:
            # Phases
            phases = trial.get("phases", [])
            for phase in phases:
                stats["phases"][phase] = stats["phases"].get(phase, 0) + 1
            
            # Status
            trial_status = trial.get("status", "Unknown")
            stats["statuses"][trial_status] = stats["statuses"].get(trial_status, 0) + 1
            
            # Study type
            study_type = trial.get("studyType", "Unknown")
            stats["studyTypes"][study_type] = stats["studyTypes"].get(study_type, 0) + 1
            
            # Sponsor
            trial_sponsor = trial.get("sponsor", "Unknown")
            stats["sponsors"][trial_sponsor] = stats["sponsors"].get(trial_sponsor, 0) + 1
            
            # Enrollment
            enrollment = trial.get("enrollment", {})
            if "count" in enrollment and enrollment["count"]:
                stats["enrollment"]["total"] += enrollment["count"]
                stats["enrollment"]["count"] += 1
            
            # Duration calculation
            dates = trial.get("dates", {})
            start_date_str = dates.get("start", "")
            completion_date_str = dates.get("completion", "")
            
            if start_date_str and completion_date_str:
                try:
                    # Parse dates - format can be "YYYY-MM-DD" or "YYYY-MM" or "YYYY"
                    def parse_date(date_str):
                        for fmt in ("%Y-%m-%d", "%Y-%m", "%B %Y", "%B %d, %Y"):
                            try:
                                return datetime.strptime(date_str, fmt)
                            except ValueError:
                                continue
                        return None
                    
                    start_date = parse_date(start_date_str)
                    completion_date = parse_date(completion_date_str)
                    
                    if start_date and completion_date and completion_date > start_date:
                        duration_days = (completion_date - start_date).days
                        stats["duration"]["total_days"] += duration_days
                        stats["duration"]["count"] += 1
                        stats["duration"]["durations"].append(duration_days)
                except Exception:
                    pass
                
        except Exception:
            continue
    
    if stats["enrollment"]["count"] > 0:
        stats["enrollment"]["average"] = stats["enrollment"]["total"] / stats["enrollment"]["count"]
    
    if stats["duration"]["count"] > 0:
        avg_days = stats["duration"]["total_days"] / stats["duration"]["count"]
        stats["duration"]["average_days"] = round(avg_days, 1)
        stats["duration"]["average_months"] = round(avg_days / 30.44, 1)
        stats["duration"]["average_years"] = round(avg_days / 365.25, 2)
        
        # Calculate min/max
        durations = stats["duration"]["durations"]
        stats["duration"]["min_days"] = min(durations)
        stats["duration"]["max_days"] = max(durations)
        
        # Remove the raw durations list to keep response compact
        del stats["duration"]["durations"]
    else:
        del stats["duration"]["durations"]
    
    return stats


def extract_sites(condition=None, phase=None, status=None, location=None, max_results=10):
    """Extract site/facility information from trials"""
    max_results = min(max_results, 20)
    
    params = {
        "format": "json",
        "pageSize": max_results
    }
    
    query_parts = []
    if condition:
        query_parts.append(f"AREA[Condition]{condition}")
    if phase:
        query_parts.append(f"AREA[Phase]{phase}")
    if status:
        query_parts.append(f"AREA[OverallStatus]{status}")
    if location:
        query_parts.append(f"AREA[LocationCountry]{location}")
    
    if query_parts:
        params["query.term"] = " AND ".join(query_parts)
    
    try:
        response = requests.get(CT_API_BASE, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        trials = data.get("studies", [])
        
        sites = []
        for trial in trials:
            protocol = trial.get("protocolSection", {})
            id_module = protocol.get("identificationModule", {})
            nct_id = id_module.get("nctId", "")
            
            contacts_module = protocol.get("contactsLocationsModule", {})
            locations = contacts_module.get("locations", [])
            
            for loc in locations:
                sites.append({
                    "nctId": nct_id,
                    "facility": loc.get("facility", "Unknown"),
                    "city": loc.get("city", ""),
                    "state": loc.get("state", ""),
                    "country": loc.get("country", ""),
                    "status": loc.get("status", ""),
                    "geoPoint": loc.get("geoPoint", {})
                })
                
                if len(sites) >= 50:
                    break
            
            if len(sites) >= 50:
                break
                
        return sites
        
    except Exception as e:
        return {"error": str(e)}
