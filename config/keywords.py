# config/keywords.py
# ?????????????????????????????????????????????????????????????
# Job keyword clusters for the scraping pipeline.
# Each cluster can be toggled on/off via ACTIVE_CLUSTERS below.
# JOB_KEYWORDS is the flat list passed to all scrapers.
# ?????????????????????????????????????????????????????????????

# ?? Toggle clusters on/off here ??????????????????????????????
ACTIVE_CLUSTERS = {
    "nhs_healthcare":        True,
    "ux_design":             True,
    "data_analytics":        True,
    "technical_engineering": True,
    "digital_marketing":     True,
    "project_ops":           True,
    "edtech":                True,
}

# ?? Cluster definitions ???????????????????????????????????????
KEYWORDS_BY_CLUSTER = {

    "nhs_healthcare": [
        # Clinical engineering / medical devices
        "Clinical Engineering Apprentice",
        "Clinical Engineering Assistant",
        "Medical Engineering Apprentice",
        "Medical Equipment Assistant",
        "Assistant Medical Devices Technologist",
        "Apprentice Assistant Clinical Technologist",
        "EBME Assistant",
        "EBME Apprentice",
        # Healthcare science
        "Healthcare Science Assistant",
        "Apprentice Healthcare Science Assistant",
        "Healthcare Science Associate",
        "Healthcare Science Apprentice",
        # Pharmacy
        "Trainee Pharmacy Technician",
        "Pre-Registration Trainee Pharmacy Technician",
        "Pharmacy Technician Apprentice",
        "Pharmacy Support Worker",
        "Pharmacy Dispenser",
        "Trainee Pharmacy Dispenser",
        "Pharmacy Assistant",
        "Dispensary Assistant",
        "Assistant Technical Officer Pharmacy",
        "Senior Assistant Technical Officer Pharmacy",
        # Sterile services / decontamination
        "Sterile Services Technician",
        "Sterile Services Assistant",
        "Trainee Sterile Services Technician",
        "Decontamination Technician",
        "Medical Device Decontamination Technician",
        "Endoscope Decontamination Technician",
        "CSSD Technician",
        "SSD Technician",
        # Prosthetics / orthotics / rehab
        "Prosthetic and Orthotic Technician",
        "Prosthetics Technician",
        "Orthotics Technician",
        "Orthotic Technician Apprentice",
        "Prosthetic Technician Apprentice",
        "Rehabilitation Engineering Technician",
        "Rehabilitation Engineering Assistant",
        "Wheelchair Service Technician",
        # Dental / medical fabrication
        "Dental Technician Trainee",
        "Dental Technician Apprentice",
        "Dental Laboratory Assistant",
        "Dental Lab Technician",
        "Maxillofacial Prosthetics Technician",
        "Orthodontic Technician Trainee",
        "CAD/CAM Dental Technician",
        # Audiology / hearing
        "Audiology Assistant",
        "Associate Audiologist",
        "Trainee Audiology Practitioner",
        "Hearing Aid Dispenser Apprentice",
        "Hearing Care Assistant",
        "Audiology Support Worker",
        "Apprentice Assistant Audiology Practitioner",
        # Neurophysiology / diagnostics
        "Neurophysiology Assistant",
        "Neurophysiology Apprentice",
        "Clinical Physiology Assistant",
        "EEG Assistant",
        "Sleep Physiology Assistant",
        "Healthcare Science Assistant Neurophysiology",
        "Assistant Clinical Physiologist Neurophysiology",
        # General NHS entry / support
        "Clinical Support Worker",
        "Healthcare Support Worker",
        "Therapy Support Worker",
        "Rehabilitation Assistant",
        "Occupational Therapy Assistant",
        "Physiotherapy Assistant",
        "Assistant Practitioner",
        # Labs / science support
        "Medical Laboratory Assistant",
        "Biomedical Support Worker",
        "Pathology Support Worker",
        "Laboratory Technician",
    ],

    "ux_design": [
        # Junior / graduate titles
        "Junior UX Designer",
        "Junior UX/UI Designer",
        "Junior Product Designer",
        "Junior Interaction Designer",
        "Junior User Researcher",
        "Junior Content Designer",
        "Junior Service Designer",
        "Graduate UX Designer",
        "Graduate UX/UI Designer",
        "Graduate Product Designer",
        # Associate titles
        "Associate UX Designer",
        "Associate Content Designer",
        "Associate Product Designer",
        "Associate User Researcher",
        # Apprenticeships
        "UX Design Apprentice",
        "UX/UI Design Apprentice",
        "Product Design Apprentice",
        "Junior UX Designer Apprentice",
        "Digital User Experience Professional",
        "User Research Apprentice",
        "Interaction Design Apprentice",
        "Service Design Apprentice",
        # Support / ops
        "Design Operations Coordinator",
        "Design Operations Assistant",
        "Product Design Intern",
    ],

    "data_analytics": [
        # Core analyst titles
        "Junior Data Analyst",
        "Graduate Data Analyst",
        "Graduate Analyst",
        "Junior BI Analyst",
        "Junior Business Intelligence Analyst",
        "Junior Reporting Analyst",
        "Junior MI Analyst",
        "Junior SQL Analyst",
        "Junior Insight Analyst",
        "Junior Operations Analyst",
        "Junior Commercial Analyst",
        "Marketing Data Analyst",
        "CRM Data Analyst",
        # UK-specific terminology
        "MI Analyst",
        "Management Information Analyst",
        "Reporting Analyst",
        "Data Reporting Analyst",
        "MI Reporting Analyst",
        "Data Operations Analyst",
        "Data Quality Analyst",
        "Data Operations Executive",
        "Analytics Assistant",
        "Data and Reporting Analyst",
        "Data Management Analyst",
        # Apprenticeships
        "Data Analyst Apprentice",
        "Junior Data Analyst Apprentice",
        "Data Technician Apprentice",
        "BI Analyst Apprentice",
        "Reporting Analyst Apprentice",
        "Analytics Apprentice",
    ],

    "technical_engineering": [
        # CAD / design
        "Junior CAD Technician",
        "CAD Designer",
        "Design Technician",
        "Junior Design Engineer",
        "Graduate Design Engineer",
        "Assistant Design Engineer",
        "Drawing Office Technician",
        "Design Office Assistant",
        # Engineering support
        "Engineering Technician",
        "Manufacturing Technician",
        "Production Technician",
        "Process Technician",
        "Production Support Technician",
        "Engineering Support Technician",
        "Mechanical Technician",
        "Workshop Technician",
        # R&D / product development
        "Product Development Technician",
        "Product Development Assistant",
        "R&D Technician",
        "R&D Assistant",
        "Prototype Technician",
        "Test Technician",
        "Development Technician",
        "Junior Product Development Technician",
        "NPI Technician",
        # Quality / technical support
        "Technical Support Engineer",
        "Technical Support Technician",
        "Quality Inspector",
        "Quality Technician",
        "QC Technician",
        "Quality Control Technician",
        # Apprenticeships
        "CAD Technician Apprentice",
        "Engineering Technician Apprentice",
        "Manufacturing Technician Apprentice",
        "Design Engineer Apprentice",
        "Junior CAD Technician Apprentice",
        "R&D Technician Apprentice",
        "Quality Technician Apprentice",
    ],

    "digital_marketing": [
        # Assistant / executive titles
        "Digital Marketing Assistant",
        "Marketing Assistant",
        "Digital Marketing Executive",
        "Social Media Assistant",
        "Social Media Executive",
        "Content Assistant",
        "Content Executive",
        "Digital Content Assistant",
        "Content Marketing Assistant",
        "CRM Assistant",
        "CRM Executive",
        "Email Marketing Assistant",
        "Email Marketing Executive",
        "Growth Marketing Assistant",
        "Marketing Coordinator",
        "Marketing Officer",
        "Digital Marketing Officer",
        "Campaign Assistant",
        "Campaign Executive",
        "Paid Media Assistant",
        "SEO Assistant",
        "E-commerce Assistant",
        "CRM Marketing Assistant",
        "Lifecycle Marketing Assistant",
        "Marketing Analytics Assistant",
        "Acquisition Assistant",
        # Apprenticeships
        "Marketing Executive Apprentice",
        "Digital Marketing Apprentice",
        "Content Creator Apprentice",
        "CRM Marketing Apprentice",
        "Email Marketing Apprentice",
        "Growth Marketing Apprentice",
    ],

    "project_ops": [
        # Coordinator / support titles
        "Project Coordinator",
        "Project Administrator",
        "Project Support Officer",
        "Project Support Coordinator",
        "Operations Assistant",
        "Operations Coordinator",
        "Programme Support Officer",
        "Programme Coordinator",
        "PMO Assistant",
        "PMO Analyst",
        "PMO Coordinator",
        "Delivery Coordinator",
        "Assistant Project Manager",
        "Project Management Administrator",
        "Project Officer",
        "Project Assistant",
        "Change Coordinator",
        "Transformation Support Officer",
        "Service Delivery Coordinator",
        "Delivery Support Officer",
        "Operations Administrator",
        "Programme Administrator",
        "Governance Coordinator",
        "Project Controls Assistant",
        "Implementation Coordinator",
        "Implementation Analyst",
        "Junior PMO Analyst",
        "Junior Operations Analyst",
        # Apprenticeships
        "Associate Project Manager Apprentice",
        "Apprentice Project Manager",
        "Project Management Apprentice",
        "PMO Apprentice",
        "Project Coordinator Apprentice",
        "Business Analyst Apprentice",
    ],

    "edtech": [
        # Learning design / technology
        "Learning Technologist",
        "Junior Learning Designer",
        "Learning Designer",
        "Instructional Designer",
        "E-learning Designer",
        "Digital Learning Designer",
        "Curriculum Designer",
        "Curriculum Design Assistant",
        "Learning Experience Designer",
        "Educational Content Designer",
        "EdTech Product Assistant",
        "Education Product Assistant",
        "Learning Design Assistant",
        "Learning Technology Assistant",
        "E-learning Specialist",
        "Learning Technology Coordinator",
        "Digital Learning Producer",
        "Online Learning Designer",
        "Learning Content Developer",
        "Educational Technologist",
        "Digital Education Assistant",
        "Learning Platform Coordinator",
        "Instructional Design Assistant",
        "Learning Systems Coordinator",
        # Apprenticeships
        "Instructional Designer Apprentice",
        "E-learning Designer Apprentice",
        "Curriculum Design Apprentice",
        "EdTech Product Apprentice",
    ],

}

# Apply operator overrides from config/keywords_override.json (gitignored)
# when present. Each override key replaces the default list for its cluster;
# unknown cluster names are ignored. Any read or parse error falls through to
# the hardcoded defaults silently so a malformed file never crashes import.
import json as _json
from pathlib import Path as _Path

_OVERRIDE_PATH = _Path("config") / "keywords_override.json"
if _OVERRIDE_PATH.is_file():
    try:
        _overrides = _json.loads(_OVERRIDE_PATH.read_text(encoding="utf-8"))
        if isinstance(_overrides, dict):
            for _cluster_name, _kw_list in _overrides.items():
                if (
                    _cluster_name in KEYWORDS_BY_CLUSTER
                    and isinstance(_kw_list, list)
                    and all(isinstance(_k, str) for _k in _kw_list)
                ):
                    KEYWORDS_BY_CLUSTER[_cluster_name] = list(_kw_list)
    except Exception:
        pass

# Flat keyword list for scrapers; rebuilt after any overrides have been
# merged so downstream consumers see the final merged set transparently.
JOB_KEYWORDS = [
    keyword
    for cluster_name, keywords in KEYWORDS_BY_CLUSTER.items()
    if ACTIVE_CLUSTERS.get(cluster_name, False)
    for keyword in keywords
]
