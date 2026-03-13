"""Add Root Cause Analysis and Lessons Learned templates, update DR links and communications."""

from django.db import migrations

DR_LINK = "[IT Disaster Recovery|https://ohsuitg.sharepoint.com/:f:/s/IT.OHSUDisasterRecovery/IgANiz5aqoEySZ1kXz3MMO8iAW6pPnPAh0NSuqyH1NQh4e4]"

COMMUNICATIONS_SECTION = """\
h2. Communications

|| Contact || Method || Number / Channel || When ||
| AOD (OHSU) | Phone | Campus Operators 503-494-8311 or direct 503-494-8105 | 15 min before start, at completion |
| AOC (HMC) | Phone | 503-681-1255 | Before start, at completion |
| NOC | Teams | NOC group chat | Before start, at completion |
| Operators | Teams | Operator group chat | Before start, at completion |
| ED Comm Center | Teams | ED Comm Center group chat | Before start, at completion |
| Poison Center | Teams | Poison Center group chat | Before start, at completion |
| Public Safety Dept | Teams | Public Safety Dept group chat | Before start, at completion |

* [ ] AOD contacted 15 minutes prior to start
* [ ] AOC notified
* [ ] NOC notified
* [ ] Operators notified
* [ ] ED Comm Center notified
* [ ] Poison Center notified
* [ ] Public Safety Dept notified
* [ ] All parties notified of completion

{expand:AOD Email Template}
Subject: Reminder: Scheduled Phone System Maintenance this Weekend

Greetings,

We have a phone system maintenance window scheduled between (DAY DATE START TIME) to (DAY DATE END TIME).

Please see the attached flyer for more information.

Per our standard operating procedure we will contact the AOD 15 minutes prior to starting our work to ensure the hospital is reasonably quiet. We will notify the AOD when the work is completed.

The EOC will be opening at (TIME).

Please let us know if you have any questions or concerns.

Thank you,

TUCE
{expand}"""

RCA_CONTENT = """\
{toc}

|| Field || Value || Field || Value ||
| Incident # | {{ incident_number|default:"(INC-XXXXXX)" }} | RCA Author | {{ rca_author|default:"(Author)" }} |
| Incident Date | {{ incident_date|default:"(DDMONYYYY HHMM)" }} | RCA Date | {{ date }} |
| Duration | {{ incident_duration|default:"(X hours X minutes)" }} | Severity | {{ severity|default:"(P1/P2/P3/P4)" }} |
| Impact | {{ impact_level|default:"(Low/Medium/High/Critical)" }} | Status | {{ rca_status|default:"(Draft/Final)" }} |

----

h2. 1. Incident Summary

{{ incident_summary|default:"(Brief description of the incident \u2014 what happened, when it was detected, and when service was restored.)" }}

----

h2. 2. Timeline of Events

|| Time || Event || Source ||
| (HH:MM) | (Incident detected / alert fired) | (Monitoring / User report) |
| (HH:MM) | (Initial response / triage began) | (On-call engineer) |
| (HH:MM) | (Root cause identified) | (Investigation) |
| (HH:MM) | (Fix applied / service restored) | (Engineer) |
| (HH:MM) | (Incident closed) | (Change ticket) |

----

h2. 3. Affected Systems

|| Device || Site || Role || Model || Primary IP ||
{% for device in devices %}| {{ device.name }} | {{ device.site.name }} | {{ device.role.name }} | {% if device.device_type %}{{ device.device_type.manufacturer.name }} {{ device.device_type.model }}{% endif %} | {{ device.primary_ip4|default:"N/A" }} |
{% endfor %}

----

h2. 4. Impact Assessment

{{ impact_assessment|default:"(Describe who and what was affected \u2014 users, services, sites, call volumes, etc.)" }}

|| Category || Details ||
| Users affected | (Number / groups affected) |
| Services affected | (List of affected services) |
| Sites affected | (List of affected sites) |
| Duration of impact | (Total user-facing downtime) |

----

h2. 5. Root Cause

{{ root_cause|default:"(Describe the root cause of the incident. Be specific \u2014 include the technical failure, configuration error, or external factor that triggered the event.)" }}

----

h2. 6. Contributing Factors

* (Contributing factor 1 \u2014 e.g., lack of monitoring, missing redundancy)
* (Contributing factor 2 \u2014 e.g., outdated firmware, documentation gap)
* (Contributing factor 3 \u2014 e.g., process not followed, insufficient testing)

----

h2. 7. Resolution

{{ resolution|default:"(Describe the steps taken to resolve the incident and restore service.)" }}

----

h2. 8. Corrective Actions

|| # || Action Item || Owner || Target Date || Status ||
| 1 | (Action item description) | (Owner) | (Date) | (Open/In Progress/Complete) |
| 2 | (Action item description) | (Owner) | (Date) | (Open/In Progress/Complete) |
| 3 | (Action item description) | (Owner) | (Date) | (Open/In Progress/Complete) |

----

h2. 9. Preventive Measures

* [ ] (Monitoring improvement \u2014 describe)
* [ ] (Process change \u2014 describe)
* [ ] (Documentation update \u2014 describe)
* [ ] (Training or knowledge share \u2014 describe)
* [ ] (Infrastructure change \u2014 describe)

----

h2. 10. Personnel Involved

|| Role || Name || Contact ||
{% for c in unique_contacts %}| {{ c.role.name|default:"(Role)" }} | {{ c.contact.name }} | {{ c.contact.phone|default:"N/A" }} |
{% endfor %}

----

h2. 11. Communications

|| Contact || Method || Number / Channel || When ||
| AOD (OHSU) | Phone | Campus Operators 503-494-8311 or direct 503-494-8105 | 15 min before start, at completion |
| AOC (HMC) | Phone | 503-681-1255 | Before start, at completion |
| NOC | Teams | NOC group chat | Before start, at completion |
| Operators | Teams | Operator group chat | Before start, at completion |
| ED Comm Center | Teams | ED Comm Center group chat | Before start, at completion |
| Poison Center | Teams | Poison Center group chat | Before start, at completion |
| Public Safety Dept | Teams | Public Safety Dept group chat | Before start, at completion |

----

h2. 12. Closeout

h3. Disaster Recovery Plan Review

* [ ] Existing DR Plan Reviewed
* [ ] Existing DR Plan \u2014 No Changes Needed
* [ ] Existing DR Plan \u2014 Changes Confirmed
* DR Plan Link: """ + DR_LINK + """
* Summary of changes: (INSERT SUMMARY HERE)

h3. System Diagram Review

* [ ] System Diagram(s) Reviewed
* [ ] Diagrams \u2014 No Changes Needed
* [ ] Diagrams \u2014 Changes Confirmed and Updated

----

_Generated: {{ date }} by {{ generated_by }}_"""

LESSONS_LEARNED_CONTENT = """\
{toc}

|| Field || Value || Field || Value ||
| Project / Incident | {{ project_name|default:"(Project or Incident Name)" }} | Author | {{ lessons_author|default:"(Author)" }} |
| Date Range | {{ date_range|default:"(Start Date \u2013 End Date)" }} | Review Date | {{ date }} |
| Category | {{ category|default:"(Project/Incident/Maintenance/Upgrade)" }} | Status | {{ review_status|default:"(Draft/Final)" }} |

----

h2. 1. Summary

{{ summary|default:"(Brief overview of the project, incident, or activity being reviewed. What was the goal and what was the outcome?)" }}

----

h2. 2. Affected Systems

|| Device || Site || Role || Model || Primary IP ||
{% for device in devices %}| {{ device.name }} | {{ device.site.name }} | {{ device.role.name }} | {% if device.device_type %}{{ device.device_type.manufacturer.name }} {{ device.device_type.model }}{% endif %} | {{ device.primary_ip4|default:"N/A" }} |
{% endfor %}

----

h2. 3. What Went Well

|| # || Item || Details ||
| 1 | (Item) | (What worked and why \u2014 be specific so it can be repeated) |
| 2 | (Item) | (Details) |
| 3 | (Item) | (Details) |

----

h2. 4. What Could Be Improved

|| # || Item || Details || Suggested Improvement ||
| 1 | (Item) | (What didn't go well and why) | (How to improve next time) |
| 2 | (Item) | (Details) | (Improvement) |
| 3 | (Item) | (Details) | (Improvement) |

----

h2. 5. Key Decisions Made

|| Decision || Rationale || Outcome ||
| (Decision 1) | (Why this was chosen) | (Result \u2014 good/bad/neutral) |
| (Decision 2) | (Rationale) | (Outcome) |

----

h2. 6. Risks Encountered

|| Risk || Was It Anticipated? || Impact || How It Was Handled ||
| (Risk 1) | (Yes/No) | (Low/Medium/High) | (Mitigation taken) |
| (Risk 2) | (Yes/No) | (Impact) | (Mitigation) |

----

h2. 7. Action Items

|| # || Action Item || Owner || Target Date || Status ||
| 1 | (Action item \u2014 process, documentation, tooling, or training improvement) | (Owner) | (Date) | (Open/In Progress/Complete) |
| 2 | (Action item) | (Owner) | (Date) | (Status) |
| 3 | (Action item) | (Owner) | (Date) | (Status) |

----

h2. 8. Recommendations

* (Recommendation 1 \u2014 changes to process, tooling, or documentation)
* (Recommendation 2 \u2014 training or knowledge sharing needs)
* (Recommendation 3 \u2014 infrastructure or monitoring improvements)

----

h2. 9. Personnel Involved

|| Role || Name || Contact ||
{% for c in unique_contacts %}| {{ c.role.name|default:"(Role)" }} | {{ c.contact.name }} | {{ c.contact.phone|default:"N/A" }} |
{% endfor %}

----

h2. 10. Closeout

h3. Disaster Recovery Plan Review

* [ ] Existing DR Plan Reviewed
* [ ] Existing DR Plan \u2014 No Changes Needed
* [ ] Existing DR Plan \u2014 Changes Confirmed
* DR Plan Link: """ + DR_LINK + """
* Summary of changes: (INSERT SUMMARY HERE)

h3. System Diagram Review

* [ ] System Diagram(s) Reviewed
* [ ] Diagrams \u2014 No Changes Needed
* [ ] Diagrams \u2014 Changes Confirmed and Updated

----

_Generated: {{ date }} by {{ generated_by }}_"""


def add_templates_and_update_existing(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")

    # --- Add new templates ---
    DocumentTemplate.objects.get_or_create(
        name="Root Cause Analysis (RCA)",
        defaults={
            "description": "Post-incident root cause analysis with timeline, impact assessment, corrective actions, and preventive measures.",
            "content": RCA_CONTENT,
        },
    )

    DocumentTemplate.objects.get_or_create(
        name="Lessons Learned",
        defaults={
            "description": "Post-project or post-incident review capturing what went well, improvements, decisions, and action items.",
            "content": LESSONS_LEARNED_CONTENT,
        },
    )

    # --- Update DR links on all existing templates ---
    old_dr_variants = [
        "* DR Plan Link: (INSERT LINK HERE)",
        "* DR Plan Link: (link)",
    ]
    new_dr = f"* DR Plan Link: {DR_LINK}"
    for t in DocumentTemplate.objects.all():
        changed = False
        # Normalize line endings
        if "\r\n" in t.content:
            t.content = t.content.replace("\r\n", "\n")
            changed = True
        for old_dr in old_dr_variants:
            if old_dr in t.content:
                t.content = t.content.replace(old_dr, new_dr)
                changed = True
        if changed:
            t.save()

    # --- Add Communications section to MOP templates that don't have it ---
    mop_names = [
        "Standard Network Change",
        "Upgrade (Multi-Phase)",
        "Firmware Upgrade MOP",
        "Decommission Plan",
        "Maintenance Reset",
    ]
    for name in mop_names:
        try:
            t = DocumentTemplate.objects.get(name=name)
        except DocumentTemplate.DoesNotExist:
            continue

        # Skip if already has the full communications table
        if "Campus Operators 503-494-8311" in t.content:
            continue

        # Find Closeout marker (numbered or unnumbered) and insert Communications before it
        import re
        match = re.search(r"h2\.\s*(\d+\.)?\s*Closeout", t.content)
        if not match:
            continue

        marker = match.group(0)
        # If numbered, bump closeout number for communications
        num_match = re.search(r"(\d+)", marker)
        if num_match:
            closeout_num = int(num_match.group(1))
            new_closeout = f"h2. {closeout_num + 1}. Closeout"
        else:
            new_closeout = marker

        insert_text = f"\n----\n\n{COMMUNICATIONS_SECTION}\n\n----\n\n{new_closeout}"
        t.content = t.content.replace(f"\n----\n\n{marker}", insert_text)
        t.save()


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_atlassian", "0017_add_interfaces_and_connections"),
    ]

    operations = [
        migrations.RunPython(
            add_templates_and_update_existing,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
